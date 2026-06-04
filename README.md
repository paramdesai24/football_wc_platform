# FIFA World Cup 2026: Simulation, Analytics & Draft Lobbies ⚽️

Welcome to the premium **FIFA World Cup 2026 Simulation & Analytics Platform**. This workspace combines advanced football analytics, live bidding auction rooms, tournament modeling, and explainable match predictions into a unified, high-performance web application.

---

## 🌟 Core Features

* **📈 Power Index & Ratings V2.1:** A state-of-the-art rating engine that calculates offensive, defensive, and composite power indexes based on goal frequency, squad valuation, player stats, clean sheets, and dynamic Elo propagation.
* **🧠 Explainable Match Predictions:** Deep simulation breakdowns offering granular advantage analysis (Attack, Defense, Elo, Form, and Overall margins) for any head-to-head match-up.
* **🎙️ Real-time Draft Lobbies:** Concurrency-safe, WebSocket-driven auction rooms allowing groups of users to nominate and bid on players live with realistic budget limits.
* **📊 Monte Carlo Lobbies:** Simulate the entire 48-team tournament up to 10,000 times to generate realistic tournament odds, trophy probabilities, and route-to-final bracket tracking.

---

## 🛠️ Architecture & Technology Stack

The platform is designed as a decoupled, multi-tier system:

* **React Frontend**: Built with React, TypeScript, and Vite. Designed using modern dark mode aesthetics, glassmorphic UI elements, and micro-animations.
* **FastAPI Backend REST & WebSocket Lobbies**: Written in Python using FastAPI for high-concurrency request routing and asynchronous WebSockets for live bidding updates.
* **Database & ORM**: PostgreSQL/SQLite schemas utilizing SQLAlchemy to manage states, draft rooms, rankings, and historical data.
* **Data-Pipeline Feature Engine**: Automates player metrics calculations, name/club entity resolution, and rating propagation.
* **Match & Tournament Engines**: Dedicated mathematical libraries for predicting matches, simulation weights, and tournament scheduling.

---

## 📂 Repository Structure

```markdown
C:\FIFA WC\
├── match_engine/          # Head-to-head score forecasting, simulator weights, and statistics
├── tournament_engine/     # Knockout structures, group standings organizers, and Monte Carlo sims
├── platform/
│   ├── backend-api/       # FastAPI REST endpoints, WebSocket controllers, schemas, and services
│   ├── frontend/          # React + TypeScript user interface (Vite & CSS v4 styling)
│   ├── data-pipeline/     # Ratings V2.1 algorithms, SQLite/Postgres exporters, and clean scripts
│   └── data/              # Authoritative databases, CSV mappings, and raw player stats
└── README.md              # Project overview (this document)
```

---

## 🚀 Quickstart Guide

Ensure you have **Node.js (LTS)** and **Python 3.11+** installed.

### 1. Start the Backend API
1. Navigate to the backend directory:
   ```powershell
   cd platform/backend-api
   ```
2. Activate the virtual environment:
   ```powershell
   ..\.venv\Scripts\activate
   ```
3. Launch the development server:
   ```powershell
   python -m uvicorn app.main:app --reload --port 8000
   ```
   *API Swagger Docs are served at `http://127.0.0.1:8000/docs`.*

### 2. Start the Frontend App
1. Open a new terminal and navigate to the frontend:
   ```powershell
   cd platform/frontend
   ```
2. Install packages:
   ```powershell
   npm install
   ```
3. Start the dev server:
   ```powershell
   npm run dev
   ```
   *Open `http://localhost:5173` to explore the interactive dashboard.*

---

## 🔒 Verification & Compliance
* **Ratings Synchronization**: Ratings calculations are verified down to a `< 0.001` floating-point tolerance between CSV files, SQLite tables, REST payloads, and the Match Engine.
* **Vite Compilation**: The frontend compiles to optimized production chunks via Rollup/Vite.
