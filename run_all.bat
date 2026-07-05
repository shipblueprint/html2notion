@echo off
REM ------------------------------------------------------------
REM Run html2notion conversion pipeline and push results to Notion
REM
REM Requires NOTION_API_KEY and NOTION_DATABASE_ID env vars.
REM Set them in your environment or in a .env file before running.
REM ------------------------------------------------------------

REM Activate virtual environment (relative path — works from any checkout)
if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else (
    echo No .venv found. Create one with: uv sync
    exit /b 1
)
set INFERENCE_RAM=6

REM Step 1: Convert PDFs/HTMLs (this script generates output JSON)
python convert_vibestack.py
if %errorlevel% neq 0 (
    echo Conversion failed with error %errorlevel%.
    exit /b %errorlevel%
)

REM Step 2: Send generated JSON payloads to Notion
if "%NOTION_API_KEY%"=="" (
    echo ERROR: NOTION_API_KEY env var is not set.
    echo Set it before running this script:
    echo   set NOTION_API_KEY=ntn_your_key_here
    exit /b 1
)
if "%NOTION_DATABASE_ID%"=="" (
    echo ERROR: NOTION_DATABASE_ID env var is not set.
    echo Set it before running this script:
    echo   set NOTION_DATABASE_ID=your_database_id_here
    exit /b 1
)

python send_to_notion.py --api-key %NOTION_API_KEY% --database-id %NOTION_DATABASE_ID%
if %errorlevel% neq 0 (
    echo Notion push failed with error %errorlevel%.
    exit /b %errorlevel%
)

echo All steps completed successfully.
pause
