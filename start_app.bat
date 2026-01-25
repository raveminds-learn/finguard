@echo off
setlocal

echo ==================================================
echo      FinGuard - Fraud Detection System
echo ==================================================

REM Check for Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    pause
    exit /b 1
)

REM Create Local Temp Directory for PIP to avoid permission issues
if not exist ".tmp" mkdir ".tmp"
set "TMP=%CD%\.tmp"
set "TEMP=%CD%\.tmp"
set "PIP_CACHE_DIR=%CD%\.tmp\pip-cache"

REM Create Virtual Environment if it doesn't exist
if not exist "venv" (
    echo [1/5] Creating virtual environment...
    python -m venv venv
) else (
    echo [1/5] Virtual environment exists.
)

REM Activate Virtual Environment
echo [2/5] Activating virtual environment...
call venv\Scripts\activate

REM Install Dependencies
echo [3/5] Checking dependencies...
echo Installing with pip...
pip install -r requirements.txt --no-cache-dir --quiet
if %errorlevel% neq 0 (
    echo Error installing dependencies. Retrying with verbose output...
    pip install -r requirements.txt --no-cache-dir
)

REM Setup Database
echo [4/5] Setting up database...
python backend/setup_db.py

REM Start Dashboard
echo [5/5] Starting FinGuard Dashboard...
echo.
echo The dashboard will open in your default browser.
echo Press Ctrl+C to stop the server.
echo.

streamlit run dashboard/app.py

endlocal
