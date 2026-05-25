# Backend API — FastAPI

This folder contains the FastAPI backend server that exposes REST endpoints used by the frontend. The service hosts tournament simulation logic, match override endpoints, country/rankings data, and related services.

Core technologies

- Python 3.10+
- FastAPI
- (SQLAlchemy is present in the codebase where needed)

Local setup

```powershell
Set-Location "C:\FIFA WC\platform\backend-api"
"C:\FIFA WC\platform\.venv\Scripts\activate"
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

API surface (high-level)

- `GET /api/v1/tournament_results` — return tournament state and simulations (supports `refresh` and `simulations` query params)
- `POST /api/v1/override_match` — apply an override and resimulate
- `POST /api/v1/resimulate_from_match` — resimulate from a specified match
- `GET /api/v1/play_as_team` — play-as-team simulation endpoints
- `GET /api/v1/countries` — country rankings and metadata

Key code locations

- `app/services/tournament_service.py` — core tournament simulation engine and defaults (UI refresh simulation counts, quick overrides)
- `app/api/v1/endpoints/tournament.py` — tournament endpoints and wrappers
- `app/api/v1/endpoints/countries.py` — country/rankings endpoint

Notes for developers

- The backend often returns wrapped payloads (e.g. `{ data: ... }`). The frontend unwraps these responses; keep the contract stable.
- There are quick/UI simulation constants in the service to limit work done for a live UI refresh. If you change simulation counts, coordinate with the frontend.

API docs are available when running locally at `http://127.0.0.1:8000/docs`.
