# FIFA World Cup 2026 Intelligence & Prediction Platform

Phase 0 monorepo foundation for a production-grade football intelligence platform.

## Scope (Phase 0)

- Monorepo architecture
- React + Vite frontend foundation
- FastAPI backend foundation
- Shared package primitives
- Data/ML module scaffolding
- Local development tooling and configuration

No ML training, analytics computation, prediction logic, or simulation implementation is included in this phase.

## Monorepo Layout

```text
platform/
  frontend/
  backend-api/
  data-pipeline/
  prediction-engine/
  simulation-engine/
  shared/
  future-auction-service/
```

## Local Development

### 1. Frontend

```powershell
cd frontend
npm install
npm run dev
```

Frontend runs on: http://localhost:3000

### 2. Backend

```powershell
cd backend-api
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs on: http://localhost:8000

### 3. Environment Variables

Copy the repository-level environment template and customize values as needed.

```powershell
copy .env.example .env
```

## Tooling

- Strict TypeScript configuration
- ESLint + Prettier for frontend
- TailwindCSS v4 design system setup
- Alembic migration preparation for backend

## Future-Ready Modules

- `data-pipeline/` for ingestion/cleaning/feature engineering/exports
- `prediction-engine/` for model lifecycle orchestration
- `simulation-engine/` for tournament Monte Carlo workflows
- `future-auction-service/` placeholder for Node.js + Socket.IO service
