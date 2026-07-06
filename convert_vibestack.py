#!/usr/bin/env python3
"""
Convert HTML files from input/ to Notion-compatible JSON in output/.
This reads HTML, injects appropriate meta tags so it's recognized
by the html2notion parser, processes it, and outputs the Notion blocks.
"""

import json
from pathlib import Path
from bs4 import BeautifulSoup
from html2notion.translate.html2json import html2json_process
from html2notion.translate.import_stats import ImportStats
from html2notion.utils import test_prepare_conf

# PDF conversion — PyMuPDF4LLM first, pdfplumber fallback
# Thanks to https://github.com/pymupdf/pymupdf4llm for the excellent
# layout-aware PDF-to-Markdown engine that powers this pipeline.
import pymupdf4llm
import markdown
from pdf_to_html import convert_pdf as pdfplumber_convert

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")


REQUIRED_META = [
    ("exporter-version", "Evernote Mac 9.6.8 (470886)"),
    ("source", "desktop.mac"),
    ("source-application", "webclipper.evernote"),
]


def prepare_html(input_path: Path) -> str:
    """Ensure HTML has YinXiang meta tags so html2notion recognizes it.
    Only adds tags that are missing — skips if already present."""
    html = input_path.read_text(encoding="utf-8")

    soup = BeautifulSoup(html, "html.parser")
    head = soup.find("head")
    if head is None:
        head = soup.new_tag("head")
        container = soup.html if soup.html else soup
        container.insert(0, head)

    existing = {m.get("name") for m in head.find_all("meta") if m.get("name")}
    for name, content in REQUIRED_META:
        if name not in existing:
            meta = soup.new_tag("meta")
            meta["name"] = name
            meta["content"] = content
            head.append(meta)

    title_tag = soup.find("title")
    if title_tag:
        title_tag.string = input_path.stem

    return str(soup)


def process_html(input_path: Path) -> dict:
    """Process a single HTML file and return Notion blocks + stats."""
    print(f"\n  Processing: {input_path.name} ...")

    modified_html = prepare_html(input_path)
    import_stats = ImportStats()
    notion_data, html_type = html2json_process(modified_html, import_stats)

    return {
        "notion_data": notion_data,
        "html_type": html_type,
        "import_stats": import_stats,
        "filename": input_path.name,
    }


def main():
    test_prepare_conf()

    # Ensure directories exist
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    all_files = sorted(INPUT_DIR.iterdir())
    for file_path in all_files:
        if file_path.is_dir():
            continue
        output_stem = file_path.stem
        output_file = OUTPUT_DIR / f"{output_stem}_notion_output.json"
        if output_file.exists():
            try:
                data = json.loads(output_file.read_text(encoding="utf-8"))
                if not data.get("children"):
                    raise ValueError("no notion blocks")
            except (json.JSONDecodeError, ValueError):
                output_file.unlink()
                print(f"  [CORRUPT] {file_path.name} — removed partial output, re-processing")
            else:
                print(f"  [SKIP] {file_path.name} — output already exists")
                continue
        is_pdf = file_path.suffix.lower() == ".pdf"
        if is_pdf:
            # Try PyMuPDF4LLM first (layout-aware, good tables)
            md_text = pymupdf4llm.to_markdown(str(file_path))
            if md_text.strip():
                body_html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])
                html_path = file_path.with_suffix(".html")
                html_content = (
                    "<!DOCTYPE html>\n<html>\n<head>\n"
                    '  <meta name="exporter-version" content="Evernote Mac 9.6.8 (470886)">\n'
                    '  <meta name="source" content="desktop.mac">\n'
                    '  <meta name="source-application" content="webclipper.evernote">\n'
                    f"  <title>{file_path.stem}</title>\n"
                    "</head>\n<body>\n"
                    f"{body_html}\n"
                    "</body>\n</html>"
                )
                html_path.write_text(html_content, encoding="utf-8")
                process_path = html_path
                print(f"  [PDF] {file_path.name} -> {html_path.name} via PyMuPDF4LLM")
            else:
                # Fallback to pdfplumber when PyMuPDF4LLM returns empty
                html_path = pdfplumber_convert(file_path)
                process_path = html_path
                print(f"  [PDF] {file_path.name} → {html_path.name} via pdfplumber (fallback)")
        else:
            process_path = file_path
            print(f"  [HTML] {file_path.name}")
        result = process_html(process_path)
        notion_data = result["notion_data"]
        import_stats = result["import_stats"]

        output_path = OUTPUT_DIR / f"{process_path.stem}_notion_output.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(notion_data, f, indent=2, ensure_ascii=False)

        print(f"  [OK] {process_path.name}")
        print(f"    Type: {result['html_type']}  |  Blocks: {len(notion_data.get('children', []))}  |  "
              f"Text: {import_stats.text_count} chars")
        if import_stats.skip_tag:
            print(f"    [WARN] Skipped tags: {len(import_stats.skip_tag)}")
        print(f"    -> {output_path.name}")
    print("=" * 60)


if __name__ == "__main__":
    main()
