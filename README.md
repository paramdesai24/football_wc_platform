# FIFA WC: Simulation & Analytics Platform ⚽️

Welcome to the ultimate playground for football fans and data analysts! This platform allows you to run full-scale World Cup simulations, draft dream squads in real-time auctions, and analyze match predictions using realistic computational engines.

---

## The Football Fan's Perspective: Build, Bid, and Conquer! 🏟️

Have you ever argued with your friends about who would win if the current World Cup was replayed 1,000 times? Or wished you could host a live, high-stakes draft to steal the best players from under your friends' noses? This platform is built for exactly that.

Here is what you can do:

* **🎙️ Live Draft Auction Rooms:** Create a draft lobby, invite your friends, and bid in real-time to sign top players. Watch the clock tick down as the price rises, manage your transfer budget, and out-bid your rivals.
* **📈 Monte Carlo Simulations:** Run the entire FIFA World Cup tournament 10,000 times. Will underdogs pull off a miracle? Will the favorites choke in the quarterfinals? See the percentage chance of every team lifting the trophy.
* **🧠 Custom Match Simulations:** Pitch any two nations against each other. Adjust tactics, respect realistic strength constraints, and generate realistic scores, goalscorers, and match statistics.

---

## 🛠️ The Developer's Perspective: Under the Hood

This is a modern, high-performance web application combining real-time communication with data-driven simulation engines.

### Technology Stack

* **Frontend:** React + TypeScript powered by Vite for an ultra-fast, responsive user experience.
* **Backend:** FastAPI (Python) hosting high-concurrency REST endpoints and live WebSocket lobbies.
* **Real-time Engine:** FastAPI WebSockets managing bidirectional traffic for instant, sub-second bidding updates in the draft lobbies.
* **Database:** PostgreSQL (with Supabase/SQLAlchemy) for keeping track of rooms, users, bidding status, historical standings, and tournament brackets.
* **Simulation Core:** Dedicated Python-based engines for match-level and tournament-level modeling.

---

## 📂 Repo Structure

* `platform/frontend/` : The React + TypeScript user interface (Vite).
* `platform/backend-api/` : FastAPI backend exposing endpoints for tournaments, matches, and real-time drafts.
* `platform/` : Consolidated platform services, environment setups, and shared utilities.
* `match_engine/` : The core module that handles head-to-head match prediction, winner probabilities, realism constraints, and score forecasting.
* `tournament_engine/` : The tournament organizer that sets fixtures, updates standings, handles knockout brackets, and executes Monte Carlo simulations.
* `DATA/` : Source databases, raw player statistics, and historical country metrics.

---

## 🚀 Quickstart Guide

### Prerequisites

* Node.js (LTS version recommended)
* Python 3.10+ (Python 3.11 recommended)

### Spin Up the Backend

1. Navigate to the backend directory:
   ```powershell
   cd platform/backend-api
   ```
2. Activate your Python virtual environment:
   ```powershell
   ..\.venv\Scripts\activate
   ```
3. Run the development server:
   ```powershell
   python -m uvicorn app.main:app --reload --port 8000
   ```
   *The interactive API documentation will be available at `http://localhost:8000/docs`.*

### Spin Up the Frontend

1. Open a new terminal and navigate to the frontend directory:
   ```powershell
   cd platform/frontend
   ```
2. Install the node packages:
   ```powershell
   npm install
   ```
3. Start the Vite development server:
   ```powershell
   npm run dev
   ```
   *Open `http://localhost:5173` in your browser to access the application.*

---

## Important Architecture Notes

* **Port Mapping:** The frontend is configured to talk to the backend on `http://127.0.0.1:8000`. You can change this by modifying the environment files.
* **Simulation Speed:** The default simulation settings for the UI are optimized for quick runs. For heavy analytical runs, check out the parameters inside `platform/backend-api/app/services/tournament_service.py`.
