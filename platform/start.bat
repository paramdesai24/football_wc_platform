@echo off
REM WC26 Intelligence Platform Startup Script

echo ========================================
echo WC26 Intelligence Platform
echo Streamlit + FastAPI Backend
echo ========================================
echo.

cd /d %~dp0

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+
    pause
    exit /b 1
)

REM Check if venv exists, create if not
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate venv
call .venv\Scripts\activate.bat

REM Install dependencies if needed
echo.
echo Installing dependencies...
pip install -q -r requirements-streamlit.txt

REM Start FastAPI backend in background
echo.
echo Starting FastAPI backend on port 8000...
start "WC26 Backend" cmd /k "cd backend-api && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to start
timeout /t 3 /nobreak

REM Start Streamlit frontend
echo.
echo Starting Streamlit frontend on port 8501...
streamlit run app.py

pause
