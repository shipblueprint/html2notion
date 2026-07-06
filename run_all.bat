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
    echo ❌ No .venv found. Create one with: uv sync
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)
set INFERENCE_RAM=6

REM Step 1: Convert PDFs/HTMLs (this script generates output JSON)
echo 📄 Step 1: Running convert_vibestack.py...
python convert_vibestack.py
if %errorlevel% neq 0 (
    echo ❌ Conversion failed with error %errorlevel%.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b %errorlevel%
)
echo ✅ Conversion completed successfully.

REM Step 2: Send generated JSON payloads to Notion
echo 📤 Step 2: Sending to Notion...

REM Check env vars first, then fall back to config.json
if "%NOTION_API_KEY%"=="" if exist config.json (
    for /f "usebackq tokens=*" %%a in (`python -c "import json; print(json.load(open('config.json'))['notion']['api_key'])"`) do set NOTION_API_KEY=%%a
)
if "%NOTION_DATABASE_ID%"=="" if exist config.json (
    for /f "usebackq tokens=*" %%a in (`python -c "import json; print(json.load(open('config.json'))['notion']['database_id'])"`) do set NOTION_DATABASE_ID=%%a
)

if "%NOTION_API_KEY%"=="" (
    echo ❌ ERROR: NOTION_API_KEY env var is not set, and config.json has no api_key.
    echo Set it before running this script:
    echo   set NOTION_API_KEY=ntn_your_key_here
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)
if "%NOTION_DATABASE_ID%"=="" (
    echo ❌ ERROR: NOTION_DATABASE_ID env var is not set, and config.json has no database_id.
    echo Set it before running this script:
    echo   set NOTION_DATABASE_ID=your_database_id_here
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

python send_to_notion.py --api-key %NOTION_API_KEY% --database-id %NOTION_DATABASE_ID%
if %errorlevel% neq 0 (
    echo ❌ Notion push failed with error %errorlevel%.
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b %errorlevel%
)

echo ✅ All steps completed successfully.
echo.
echo Press any key to exit...
pause >nul