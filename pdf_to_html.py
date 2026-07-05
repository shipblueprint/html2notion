#!/usr/bin/env python3
"""
Convert PDF files from input/ to clean HTML (with YinXiang meta tags)
so they can be processed by html2notion and pushed to Notion.

Uses pdfplumber for robust table detection with correct cell content.
Table regions are excluded from plain-text output to avoid duplication.

Usage:
    .venv/Scripts/python pdf_to_html.py
"""

import re
from pathlib import Path

import pdfplumber

INPUT_DIR = Path("input")


def html_escape(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\n", "<br>")
    text = re.sub(r"(<br>\s*){3,}", "<br><br>", text)
    return text.strip()


def extract_tables_html(page, min_rows=2) -> tuple[str, list]:
    """
    Extract tables from a pdfplumber page and return:
      - HTML string of all tables
      - list of (x0, top, x1, bottom) bboxes covering all table cells
    Returns ('', []) if no tables found.
    """
    tables = page.find_tables()
    if not tables:
        return "", []

    parts = []
    all_bboxes = []
    for table in tables:
        data = table.extract()
        if not data or len(data) < min_rows:
            continue
        # Collect all cell bboxes
        for row in table.rows:
            for cell in row.cells:
                # cell is a tuple (x0, top, x1, bottom)
                all_bboxes.append(cell)

        parts.append("    <table>")
        for row_idx, row in enumerate(data):
            tag = "th" if row_idx == 0 else "td"
            parts.append("      <tr>")
            for cell in row:
                cell_text = html_escape(str(cell).strip() if cell else "")
                parts.append(f"        <{tag}>{cell_text}</{tag}>")
            parts.append("      </tr>")
        parts.append("    </table>")

    return "\n".join(parts), all_bboxes


def extract_non_table_text(page, table_bboxes) -> list[str]:
    """
    Extract text from the page, excluding content that falls within
    any table cell's bounding box.  Uses pdfplumber character-level data.
    """
    if not page.chars:
        return []

    # Build a list of words with their bounding boxes
    words = page.extract_words(keep_blank_chars=False, x_tolerance=3)
    if not words:
        return []

    # Filter out words that are inside any table cell
    filtered_words = []
    for w in words:
        cx = (w["x0"] + w["x1"]) / 2
        cy = (w["top"] + w["bottom"]) / 2
        in_table = False
        for bx0, btop, bx1, bbottom in table_bboxes:
            if (bx0 - 2 <= cx <= bx1 + 2) and (btop - 2 <= cy <= bbottom + 2):
                in_table = True
                break
        if not in_table:
            filtered_words.append(w["text"])

    # Reconstruct lines from remaining words
    # Use original page text lines as reference, but only keep lines
    # where most words are outside table cells
    raw_text = page.extract_text()
    if not raw_text:
        return []

    lines = raw_text.split("\n")
    result = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        # Skip page numbers and running headers
        if re.match(r"^\d+\s*$", line):
            continue
        if "Corporate Autopsy SOP" in line and len(line) < 60:
            continue
        if len(line) <= 1:
            continue
        result.append(line)

    return result


def merge_paragraphs(lines: list[str]) -> list[str]:
    """Merge text lines into paragraphs."""
    if not lines:
        return []

    paragraphs = []
    current = [lines[0]]
    for line in lines[1:]:
        # If previous line ended without period/colon and this line starts
        # with lowercase or is short, it's a continuation
        prev = current[-1]
        if (not prev.endswith((".", "?", "!", ":")) and
                (line[0].islower() or len(line) < len(prev) * 0.6)):
            current.append(line)
        elif len(prev) < 40 and len(line) < 40:
            # Both short lines - probably a list or heading, keep on same line
            current.append(line)
        else:
            paragraphs.append(" ".join(current))
            current = [line]
    if current:
        paragraphs.append(" ".join(current))
    return paragraphs


def convert_pdf(pdf_path: Path) -> Path:
    """Convert a PDF to HTML with tables and clean non-table text."""
    print(f"\n  Converting: {pdf_path.name} ...")

    title = pdf_path.stem
    html_parts = [
        "<!DOCTYPE html>",
        "<html>",
        "<head>",
        f"  <title>{title}</title>",
        '  <meta name="exporter-version" content="Evernote Mac 9.6.8 (470886)">',
        '  <meta name="source" content="desktop.mac">',
        '  <meta name="source-application" content="webclipper.evernote">',
        "</head>",
        "<body>",
    ]

    total_tables = 0

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_parts = []

            # 1. Extract tables with their bounding boxes
            table_html, table_bboxes = extract_tables_html(page, min_rows=2)
            if table_html:
                page_parts.append(table_html)
                total_tables += table_html.count("<table>")

            # 2. Extract non-table text
            text_lines = extract_non_table_text(page, table_bboxes)
            if text_lines:
                paragraphs = merge_paragraphs(text_lines)
                for para in paragraphs:
                    page_parts.append(f"    <p>{html_escape(para)}</p>")

            if page_parts:
                html_parts.append(f"  <!-- PAGE {page_num + 1} -->")
                html_parts.extend(page_parts)

    html_parts.append("</body>")
    html_parts.append("</html>")

    html_path = pdf_path.with_suffix(".html")
    html_path.write_text("\n".join(html_parts), encoding="utf-8")
    print(f"    Pages: {len(pdf.pages)}, Tables: {total_tables}")
    print(f"    Written: {html_path.name}")
    return html_path


def main():
    INPUT_DIR.mkdir(exist_ok=True)
    pdf_files = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No .pdf files found in {INPUT_DIR}/")
        return
    print("=" * 60)
    print(f"  PDF -> HTML Converter -- {len(pdf_files)} file(s)")
    print("=" * 60)
    for pdf_path in pdf_files:
        convert_pdf(pdf_path)
    print("\nDone! Run next:")
    print("  .venv/Scripts/python convert_vibestack.py")
    print("  .venv/Scripts/html2notion --conf config.json --dir input")


if __name__ == "__main__":
    main()
