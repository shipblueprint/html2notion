#!/usr/bin/env python3
"""
MCP server for html2notion — PDF/HTML → Notion JSON blocks.
Run with: mcp run mcp_server.py
Or for dev: mcp dev mcp_server.py
"""

from pathlib import Path
from mcp.server.fastmcp import FastMCP
from html2notion.translate.html2json import html2json_process
from html2notion.translate.import_stats import ImportStats
from html2notion.utils import test_prepare_conf
from convert_vibestack import prepare_html, REQUIRED_META
import pymupdf4llm
import markdown

mcp = FastMCP("html2notion")
test_prepare_conf()


@mcp.tool()
def convert_pdf(pdf_path: str) -> list:
    """Convert a PDF file to Notion-compatible JSON blocks.

    Args:
        pdf_path: Absolute or relative path to the PDF file.
    Returns:
        List of Notion block objects suitable for the Notion API.
    """
    path = Path(pdf_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"PDF not found: {path}")

    md_text = pymupdf4llm.to_markdown(str(path))
    if not md_text.strip():
        raise ValueError(f"PyMuPDF4LLM returned empty content for {path.name}")

    body_html = markdown.markdown(md_text, extensions=["tables", "fenced_code"])

    # Wrap in proper HTML with meta tags so html2notion uses the YinXiang parser
    meta_tags = "\n".join(
        f'  <meta name="{name}" content="{content}">' for name, content in REQUIRED_META
    )
    html_content = (
        "<!DOCTYPE html>\n<html>\n<head>\n"
        f"{meta_tags}\n"
        f"  <title>{path.stem}</title>\n"
        "</head>\n<body>\n"
        f"{body_html}\n"
        "</body>\n</html>"
    )

    stats = ImportStats()
    notion_data, _ = html2json_process(html_content, stats)
    return notion_data.get("children", [])


@mcp.tool()
def convert_html(html_path: str) -> list:
    """Convert an HTML file to Notion-compatible JSON blocks.

    Args:
        html_path: Absolute or relative path to the HTML file.
    Returns:
        List of Notion block objects suitable for the Notion API.
    """
    path = Path(html_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"HTML not found: {path}")

    modified_html = prepare_html(path)
    stats = ImportStats()
    notion_data, _ = html2json_process(modified_html, stats)
    return notion_data.get("children", [])


if __name__ == "__main__":
    mcp.run()
