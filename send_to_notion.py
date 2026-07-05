#!/usr/bin/env python3
"""
Send pre-generated JSON from output/ to Notion via the API.
Usage:
    python send_to_notion.py --api-key ntn_... --database-id <id> [--input output/some_file.json]
"""

import json
import argparse
import asyncio
from pathlib import Path
from notion_client import AsyncClient

OUTPUT_DIR = Path("output")


async def main():
    parser = argparse.ArgumentParser(description="Send Notion JSON payload to Notion API")
    parser.add_argument("--api-key", required=True, help="Notion integration token (ntn_...)")
    parser.add_argument("--database-id", required=True, help="Notion database ID")
    parser.add_argument("--input", help="Input JSON file (default: output/*_notion_output.json)")
    args = parser.parse_args()

    # Find input files
    if args.input:
        input_paths = [Path(args.input)]
    else:
        input_paths = sorted(OUTPUT_DIR.glob("*_notion_output.json"))

    if not input_paths:
        print(f"No input files found. Put JSON in {OUTPUT_DIR}/ or use --input")
        return

    async with AsyncClient(auth=args.api_key) as notion:
        for input_path in input_paths:
            if not input_path.exists():
                print(f"✗ {input_path} not found, skipping")
                continue

            with open(input_path, encoding="utf-8") as f:
                payload = json.load(f)

            # Inject database ID
            payload["parent"]["database_id"] = args.database_id

            children = payload.pop("children", [])
            title = payload.get("properties", {}).get("Title", {}).get("title", [{}])
            title_text = title[0].get("text", {}).get("content", "Untitled") if title else "Untitled"

            print(f"\n  Sending: {input_path.name}")
            print(f"  Title:   {title_text}")
            print(f"  Blocks:  {len(children)}")

            # Notion API limit: 100 blocks per request
            chunk_size = 100
            first_chunk = children[:chunk_size]
            remaining = children[chunk_size:]

            created_page = await notion.pages.create(**payload, children=first_chunk)
            page_id = created_page["id"]
            print(f"  [OK] Page created: https://www.notion.so/{page_id.replace('-', '')}")

            for i in range(0, len(remaining), chunk_size):
                chunk = remaining[i : i + chunk_size]
                await notion.blocks.children.append(page_id, children=chunk)
                print(f"  [OK] Appended blocks {i + chunk_size + 1}–{min(i + chunk_size * 2, len(children))}")

    print("\nDone!")


if __name__ == "__main__":
    asyncio.run(main())
