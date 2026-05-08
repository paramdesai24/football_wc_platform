# Backend API (Phase 0)

FastAPI service foundation for the FIFA World Cup 2026 Intelligence & Prediction Platform.

## Stack

- FastAPI
- SQLAlchemy
- SQLite (initial local database)
- Alembic migration preparation

## Local Setup

1. Create and activate virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Run API

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

4. API Docs

- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Migration Preparation

Alembic structure is initialized for future schema versioning.

```powershell
alembic revision -m "init schema"
alembic upgrade head
```

## Architecture

```text
app/
  api/
    v1/
  core/
  jobs/
  models/
  repositories/
  schemas/
  services/
  utils/
```

This phase does not include ML model serving or prediction logic implementation.
