@echo off
REM WC26 Intelligence Platform Startup Script

echo ========================================
echo WC26 Intelligence Platform
echo React + FastAPI Backend
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

REM Start FastAPI backend in background
echo Starting FastAPI backend on port 8000...
start "WC26 Backend" cmd /k "cd backend-api && call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Wait for backend to start
timeout /t 3 /nobreak

REM Start Vite React frontend
echo.
echo Starting React frontend on port 3000...
start "WC26 Frontend" cmd /k "cd frontend && npm run dev"

pause
