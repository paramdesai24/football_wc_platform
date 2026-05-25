## FIFA WC — Simulation & Analytics

This repository contains a tournament simulation and analytics application. It includes a React + TypeScript frontend (Vite) and a FastAPI backend service that runs tournament simulations, exposes REST endpoints, and hosts simulation services used by the UI.

This README is a high-level overview. For detailed developer notes see `PROJECT_STATUS.md`.

## Repo layout

- `platform/frontend/` — React + TypeScript UI (Vite)
- `platform/backend-api/` — FastAPI backend with simulation services
- `platform/` — other platform services and utilities
- `archive/` — legacy artifacts (kept for reference)
- `DATA/` — source data used by simulation (CSV, raw assets)

## Quickstart (development)

Prerequisites:
- Node.js (recommended LTS)
- Python 3.10+ and virtual environment tooling

Start the backend (from repo root):

```powershell
Set-Location "C:\FIFA WC\platform\backend-api"
"C:\FIFA WC\platform\.venv\Scripts\activate"
python -m uvicorn app.main:app --reload --port 8000
```

Start the frontend (in a separate terminal):

```powershell
Set-Location "C:\FIFA WC\platform\frontend"
npm install
npm run dev
```

Build for production:

```powershell
Set-Location "C:\FIFA WC\platform\frontend"
npm run build

Set-Location "C:\FIFA WC\platform\backend-api"
"C:\FIFA WC\platform\.venv\Scripts\activate"
python -m uvicorn app.main:app --port 8000
```

## Important notes
- The frontend expects the backend REST API under `/api/v1/*` (defaults to `http://127.0.0.1:8000` in development unless overridden in environment variables).
- The backend includes quick/UI simulation defaults (small number of simulations) to keep the UI responsive. See `platform/backend-api/app/services/tournament_service.py` for the constants and behavior.
- Keep `README.md` (this file) and `PROJECT_STATUS.md` (high level project status) in the root — other README files across the workspace have been consolidated.

## Project status
See `PROJECT_STATUS.md` for current status, recent changes, and notes about ongoing UI/engine work.

---
If you need details about the frontend or backend individually, consult the README files in `platform/frontend/` and `platform/backend-api/`.
