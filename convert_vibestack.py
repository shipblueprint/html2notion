#!/usr/bin/env python3
"""
Convert HTML files from input/ to Notion-compatible JSON in output/.
This reads HTML, injects appropriate meta tags so it's recognized
by the html2notion parser, processes it, and outputs the Notion blocks.
"""

import json
import os
import sys
from pathlib import Path
from collections import Counter
from bs4 import BeautifulSoup
from html2notion.translate.html2json import html2json_process
from html2notion.translate.import_stats import ImportStats
from html2notion.utils import test_prepare_conf

# Imports for PDF conversion using marker-pdf
from marker.converters.pdf import PdfConverter
# Set environment variable to inform Marker of available VRAM (in GB)
# This helps it allocate memory conservatively.
os.environ.setdefault('INFERENCE_RAM', '6')
from marker.models import create_model_dict
from marker_wrapper import decide_file_type

INPUT_DIR = Path("input")
OUTPUT_DIR = Path("output")


def prepare_html(input_path: Path) -> str:
    """Read HTML and inject YinXiang-compatible meta tags so the parser
    recognizes it as an Evernote export for optimal block conversion."""
    html = input_path.read_text(encoding="utf-8")

    soup = BeautifulSoup(html, "html.parser")
    head = soup.find("head")
    if head is None:
        head = soup.new_tag("head")
        soup.html.insert(0, head)

    meta_tags = [
        ("exporter-version", "Evernote Mac 9.6.8 (470886)"),
        ("source", "desktop.mac"),
        ("source-application", "webclipper.evernote"),
    ]
    for name, content in meta_tags:
        meta = soup.new_tag("meta")
        meta["name"] = name
        meta["content"] = content
        head.append(meta)

    # Use the file name (without extension) as the page title
    title_tag = soup.find("title")
    if title_tag:
        title_tag.string = input_path.stem

    return str(soup)


def fix_table_blocks(children: list) -> list:
    """
    The html2notion library's convert_table() returns blocks missing the
    "type": "table" field.  The Notion API requires:
      {"type": "table", "table": {...}}
    This fixes any table blocks that lack the type field.
    """
    fixed = []
    for block in children:
        # If block has "table" key but no "type" key, add it
        if "table" in block and "type" not in block:
            block["type"] = "table"
            block["object"] = "block"
        # Also fix nested table children
        if "table" in block and "children" in block["table"]:
            block["table"]["children"] = fix_table_blocks(block["table"]["children"])
        fixed.append(block)
    return fixed


def process_html(input_path: Path) -> dict:
    """Process a single HTML file and return Notion blocks + stats."""
    print(f"\n  Processing: {input_path.name} ...")

    modified_html = prepare_html(input_path)
    import_stats = ImportStats()
    notion_data, html_type = html2json_process(modified_html, import_stats)

    # Fix table blocks (the library omits "type": "table")
    if "children" in notion_data:
        notion_data["children"] = fix_table_blocks(notion_data["children"])

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
    all_results = []
    # ==== Unified processing loop ==== 
    all_files = sorted(INPUT_DIR.iterdir())
    for file_path in all_files:
        if file_path.is_dir():
            continue
        output_stem = file_path.stem
        if (OUTPUT_DIR / f"{output_stem}_notion_output.json").exists():
            print(f"  [SKIP] {file_path.name} — output already exists")
            continue
        # Decide using LLM marker
        file_type = decide_file_type(file_path)
        if file_type == "pdf":
            # Convert PDF using Marker‑PDF (v1.10.2)
            converter = PdfConverter(
                artifact_dict=create_model_dict(),
                config={
                    "output_format": "html",
                    # Reduce parallel workers to limit per‑worker VRAM usage
                    "max_workers": 1,
                    # Lower batch multiplier to further reduce memory footprint
                    "batch_multiplier": 1,
                },
            )
            rendered = converter(str(file_path))
            html_content = getattr(rendered, "html", "")
            html_path = file_path.with_suffix(".html")
            html_path.write_text(html_content, encoding="utf-8")
            process_path = html_path
            print(f"  [LLM] {file_path.name} classified as PDF -> converting to {html_path.name} using Marker‑PDF")
        else:
            process_path = file_path
            print(f"  [LLM] {file_path.name} classified as HTML -> processing directly")
        result = process_html(process_path)
        all_results.append(result)

        notion_data = result["notion_data"]
        import_stats = result["import_stats"]
        stem = process_path.stem

        # Write full Notion API payload
        output_path = OUTPUT_DIR / f"{stem}_notion_output.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(notion_data, f, indent=2, ensure_ascii=False)

        # Write stats
        stats = {
            "filename": stem,
            "html_type": result["html_type"],
            "block_count": len(notion_data.get("children", [])),
            "text_chars": import_stats.text_count,
            "notion_text_chars": import_stats.notion_text_count,
            "image_count": import_stats.image_count,
            "notion_image_count": import_stats.notion_image_count,
            "skipped_tags": import_stats.skip_tag,
            "database_id": notion_data.get("parent", {}).get("database_id", "N/A"),
        }
        stats_path = OUTPUT_DIR / f"{stem}_notion_stats.json"
        with open(stats_path, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        # Print per‑file summary
        block_types = Counter()
        for block in notion_data.get("children", []):
            block_types[block.get("type", "unknown")] += 1

        print(f"  [OK] {process_path.name}")
        print(f"    Type: {result['html_type']}  |  Blocks: {len(notion_data.get('children', []))}  |  "
              f"Text: {import_stats.text_count} chars")
        if import_stats.skip_tag:
            print(f"    [WARN] Skipped tags: {len(import_stats.skip_tag)}")
        print(f"    -> {output_path.name}")
        print(f"    -> {stats_path.name}")

    # Full summary
    total_blocks = sum(len(r["notion_data"].get("children", [])) for r in all_results)
    total_text = sum(r["import_stats"].text_count for r in all_results)

    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    print(f"  Files processed: {len(all_results)}")
    print(f"  Total blocks:    {total_blocks}")
    print(f"  Total text:      {total_text} chars")
    print(f"\n  Input:  {INPUT_DIR.resolve()}")
    print(f"  Output: {OUTPUT_DIR.resolve()}")
    print(f"\n  To push to Notion, run:")
    print(f"    html2notion --conf config.json --dir {INPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
