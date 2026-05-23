# WC26 Intelligence Platform - Minimal Streamlit Frontend

This is a **temporary, minimal frontend** created during a frontend reset phase. It provides basic UI for the backend systems while we prepare for a professional redesign.

## Current Status

✓ Backend systems fully preserved  
✓ APIs intact  
✓ Prediction engines ready  
✓ Minimal UI for data display  

## Running the Application

### Prerequisites
- Python 3.11+
- Backend API running on `http://localhost:8000`

### Installation

```bash
# Navigate to platform directory
cd platform

# Install Streamlit dependencies
pip install -r requirements-streamlit.txt
```

### Start the Application

```bash
# Run Streamlit app
streamlit run app.py
```

The application will open at `http://localhost:8501`

### Start scripts (Windows / Unix)

Use the provided startup scripts to start backend + frontend together.

Windows (from `platform/`):

```powershell
.\start.bat
```

Unix / macOS (from `platform/`):

```bash
./start.sh
```

## Features

- **Dashboard**: Tournament overview and system status
- **Predictions**: Match prediction interface
- **Rankings**: Global team rankings
- **Analytics**: Team statistics and analysis
- **Tournament**: Tournament simulation and results

## Architecture

```
platform/
├── app.py                        # Main Streamlit application
├── requirements-streamlit.txt    # Streamlit dependencies
├── backend-api/                  # FastAPI backend (PRESERVED)
│   ├── app/
│   └── requirements.txt
├── data-pipeline/               # Data processing (PRESERVED)
└── shared/                       # Shared utilities (PRESERVED)
```

## Notes

- This UI is **temporary and minimal**
- No animations, complex CSS, or unnecessary styling
- Focus is on stable functionality
- Ready for professional redesign later

## Backend Integration

The Streamlit app connects to:
- FastAPI backend on port 8000
- Prediction systems
- Ranking calculations
- Tournament simulations
- Analytics engines

All backend systems remain fully intact and functional.
