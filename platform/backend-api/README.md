# FastAPI Backend Service

This is the high-performance backend application powering the Football Intelligence Platform. It exposes the REST API layer and bid-direction WebSocket connections for the real-time draft system.

---

## 🛠️ Key Technologies

* **FastAPI**: Asynchronous routing, middleware validation, and speed.
* **SQLAlchemy & SQLite/Postgres**: Database engines, schema declaration, and migrations.
* **Pydantic**: Request and response schema contracts.
* **WebSockets**: Concurrency-safe, real-time draft state broadcasts.

---

## 📂 Directory Layout

```markdown
platform/backend-api/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/       # Route controllers (analytics, predictions, draft, etc.)
│   │   └── router.py        # Central API router mapping
│   ├── core/                # DB connection, configurations, and core setup
│   ├── models/              # SQLAlchemy model definitions (Draft, Match, User)
│   ├── schemas/             # Pydantic data validation schemas
│   └── services/            # Simulation engines & draft business logic wrappers
├── app.db                   # Main SQLite database location (local development)
└── README.md                # Backend service overview
```

---

## 📡 Essential REST API Endpoints

### 1. Analytics & Ratings V2.1
* **`GET /api/v1/analytics/team/{country_id}`**: Returns comprehensive ratings, recent form, and detailed offensive/defensive component breakdowns.
* **`GET /api/v1/countries/rankings`**: Serves the active power ranks, indexes, and Elo ratings for all qualified nations.

### 2. Match Predictor & Explainability
* **`POST /api/v1/predictions/predict`**: Predicts scorelines between any two nations. Includes `advantage_breakdown` (Attack, Defense, Elo, Form, and Overall margins).
* **`GET /api/v1/predictions`**: Accesses prediction logs and historic simulator outputs.

### 3. Tournament Simulations
* **`GET /api/v1/tournament_results`**: Organizes knockout brackets and returns Monte Carlo outcomes.
* **`POST /api/v1/override_match`**: Applies user scores to custom fixtures and dynamically triggers downstream calculations.

### 4. Real-time Lobbies
* **`GET /api/v1/leagues/{league_id}`**: Retrieves league rules, participant structures, and rosters.
* **`WS /api/v1/ws/auction/{league_id}/{user_id}`**: Livelink socket for draft nominations and bid inputs.

---

## 🚀 Running the Server Locally

1. Navigate to the backend directory:
   ```powershell
   cd platform/backend-api
   ```
2. Activate your Python virtual environment:
   ```powershell
   ..\.venv\Scripts\activate
   ```
3. Boot the development server:
   ```powershell
   python -m uvicorn app.main:app --reload --port 8000
   ```
   *The interactive API documentation is served at `http://localhost:8000/docs`.*
