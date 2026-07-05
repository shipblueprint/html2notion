# html2notion

A powerful conversion pipeline that transforms **HTML** (or **PDF**) files into Notion‑compatible JSON payloads and pushes them directly to a Notion database.

## Features
- **HTML ↔ Notion** – Uses the original `html2notion` library for high‑fidelity block conversion.
- **PDF support via Marker‑PDF 1.10.2** – Automatic PDF → HTML conversion with optional GPU memory control.
- **GPU‑friendly** – You can limit VRAM usage (e.g., 6 GB) via the `INFERENCE_RAM` environment variable and `max_workers` / `batch_multiplier` settings.
- **Batch processing** – Handles an entire `input/` folder and writes per‑file JSON and statistics to `output/`.
- **One‑click Notion sync** – Sends everything to Notion using a simple CLI.

## Quick start
```bash
# Clone your fork (already done locally)
cd html2notion

# Create a virtual environment (optional but recommended)
python -m venv .venv && .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration
1. **Notion credentials** – Edit `config.json` or pass them via the command line:
   ```json
   {
     "notion_api_key": "YOUR_NOTION_API_KEY",
     "database_id": "YOUR_DATABASE_ID"
   }
   ```
2. **GPU memory limit** – Set `INFERENCE_RAM` (in GB) before running the pipeline. The provided `run_all.bat` already does this:
   ```bat
   set INFERENCE_RAM=6
   ```
3. **Marker‑PDF options** – Adjust inside `convert_vibestack.py` if you need different `max_workers` or `batch_multiplier`.

## Usage
### 1️⃣ Convert files (HTML + PDF)
Place your source files in the `input/` directory and run:
```bat
run_all.bat
```
The script will:
- Activate the virtual environment.
- Convert PDFs using Marker‑PDF (respecting the 6 GB VRAM limit).
- Process HTML files with `html2notion`.
- Write `*_notion_output.json` and `*_notion_stats.json` to the `output/` folder.

### 2️⃣ Push to Notion
`run_all.bat` automatically calls `send_to_notion.py` with the API key and database ID from your fork’s config.

## Advanced options
- **Force OCR on PDFs** – Add `--force_ocr` to the Marker‑PDF config if your PDFs are scanned images.
- **Batch size** – Lower `batch_multiplier` in `convert_vibestack.py` to reduce memory at the cost of speed.
- **Parallel workers** – Change `max_workers` (default 1) for faster conversion on machines with more VRAM.

## Contributing
Feel free to open issues or submit pull requests. Please keep the following in mind:
- Stick to the existing coding style (PEP 8, type hints).
- Update the README if you add new features or flags.
- Ensure the pipeline still works on both Windows and Unix‑like environments.

## License
This project is licensed under the MIT License – see the `LICENSE` file for details.

<p align="center">
  <a href="https://github.com/selfboot/html2notion/actions/workflows/python-package.yml">
    <img src="https://github.com/selfboot/html2notion/actions/workflows/python-package.yml/badge.svg" alt="CI Test Status">
  </a>
 <a href="https://codecov.io/gh/selfboot/html2notion" >
 <img src="https://codecov.io/gh/selfboot/html2notion/branch/master/graph/badge.svg?token=SIM6I7BZU6" alt="Test coverage"/>
 </a>
</p>

html2notion is an incredibly useful tool written in Python, which allows you to import content from HTML documents into Notion notes, making it more convenient for you to organize information on the Notion platform. In addition, html2notion has been specifically optimized for the content of Evernote, and you can also use it to import notes from Evernote into Notion.

html2notion has powerful features and supports converting various tags in HTML files into corresponding Blocks in Notion, such as rich text blocks, headings, images, code blocks, quotes, links, etc. Below are examples of converting notes from Evernote into Notion pages.

![yinxiang notion(simple demos)](https://raw.githubusercontent.com/selfboot/html2notion/master/demos/yinxiang_notion.png)

![yinxiang notion2(rich text)](https://raw.githubusercontent.com/selfboot/html2notion/master/demos/yinxiang_notion2.png)

# Prepare

You only need 3 steps to use htmlnotion to import HTML into Notion.

## Duplicate database

Click the link [notion template](https://selfboot.notion.site/selfboot/130bb48c6cbd4abbbb713d4d8472481a?v=ddda20d3f46b4b44a055d06792c142f0). As shown in the image below, use the "Duplicate" button to copy a new database to your own Notion workspace.

![notion template](https://raw.githubusercontent.com/selfboot/html2notion/master/demos/notion_templage.png)

## Install html2notion

Requires python>=3.8, install the html2notion library. You can use the pip command to install it:

```
pip install html2notion
```

## Prepare Notion Configuration

We need to use the `Notion API key` and `Database ID` to authorize html2notion to access the Notion database. Please follow these steps:

1. Create an integration;
2. Share a database with your integration;
3. Export the database ID;

When sharing the database here, you need to choose the previously duplicated database because the import operation requires some preset [properties](https://developers.notion.com/reference/property-object) information in this database.

For specific methods, please refer to the Notion official documentation [create an integration](https://developers.notion.com/docs/create-a-notion-integration).

After the setup is complete, write your API Key and database ID into a configuration file config.json.

```shell
{
    "notion": {
        "database_id": "<***demo***>",
        "api_key": "<***demo***>"
    }
}
```

# Usage

You can use `html2notion -h` to view detailed help documentation.

```shell
usage: html2notion [-h] --conf CONF [--log LOG] [--batch BATCH] (--file FILE | --dir DIR)

Html2notion: Save HTML to your Notion notes quickly and easily, while keeping the original format as much as possible

options:
  -h, --help     show this help message and exit
  --conf CONF    conf file path
  --log LOG      log direct path
  --batch BATCH  batch save concurrent limit
  --file FILE    Save single html file to notion
  --dir DIR      Save all html files in the dir to notion
```

For example, if you want to import all html files in the `./demos` directory into Notion, you can use the following command:

```shell
html2notion --conf config.json --dir ./demos --log ~/logs --batch 10
```

The above command will import all html files in the `./demos` directory into Notion, while outputting logs to the `~/logs` directory, with up to 10 concurrent tasks.

# More information

You can find more information and examples in the html2notion library's Issue: [html2notion](https://github.com/selfboot/html2notion/issues)

## Contribution

If you find any errors or have any suggestions for improvement, please do not hesitate to submit a pull request or raise an issue, I am more than happy to accept your contributions and feedback!

If you encounter import failures, you can submit the html file and log file together in the issue for easier problem identification.

> If there are any private information in the files, please remove it first.


## License

This project uses the MIT license. Please refer to the [LICENSE](./LICENSE) for details.
