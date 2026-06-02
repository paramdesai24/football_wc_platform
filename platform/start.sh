#!/bin/bash

# WC26 Intelligence Platform Startup Script

echo "========================================"
echo "WC26 Intelligence Platform"
echo "React + FastAPI Backend"
echo "========================================"
echo ""

cd "$(dirname "$0")"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found. Please install Python 3.11+"
    exit 1
fi

# Start FastAPI backend in background
echo ""
echo "Starting FastAPI backend on port 8000..."
(cd backend-api && source .venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload) &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start React frontend
echo ""
echo "Starting React frontend on port 3000..."
(cd frontend && npm run dev)

# Cleanup on exit
trap "kill $BACKEND_PID" EXIT
