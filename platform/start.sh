#!/bin/bash

# WC26 Intelligence Platform Startup Script

echo "========================================"
echo "WC26 Intelligence Platform"
echo "Streamlit + FastAPI Backend"
echo "========================================"
echo ""

cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Check if venv exists, create if not
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies if needed
echo ""
echo "Installing dependencies..."
pip install -q -r requirements-streamlit.txt

# Start FastAPI backend in background
echo ""
echo "Starting FastAPI backend on port 8000..."
(cd backend-api && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload) &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start Streamlit frontend
echo ""
echo "Starting Streamlit frontend on port 8501..."
streamlit run app.py

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
