# React + TypeScript Frontend

This directory houses the modern, high-fidelity single-page application (SPA) built for the FIFA World Cup 2026 Simulation & Analytics Platform.

---

## 🏆 User Features

* **Real-time Live Auction Room**: A premium WebSocket-driven draft interface where managers bid on a pool of over 1,100 players in real-time, managing budgets and strict roster/position caps.
* **Attacking & Defensive Profiles**: Premium analytics cards visualizing detailed components of offensive scoring frequency, backline market depth, shutout consistency, and goalkeeper metrics.
* **Explainable Match Predictor**: Shows win probability margins alongside interactive explanation breakdowns (Attack, Defense, Elo, Form, and Overall composite advantages).
* **Monte Carlo Simulator**: Runs 10,000 simulations of the World Cup tournament, displaying live qualifications, standings updates, and dynamic bracket maps.

---

## 🛠️ Technology Stack

* **React 19 & TypeScript**: Component structure, hooks lifecycle, and contract interfaces.
* **Vite 8 & Tailwind CSS / Vanilla CSS**: Ultra-fast bundler, Tailwind v4 styling utilities, and global design variables located in `src/styles/globals.css`.
* **Zustand 5**: Decoupled, high-performance state management for draft room caches and user sessions.
* **ECharts**: High-fidelity data visualization charts and progress plots.

---

## 📂 Code Organization

```markdown
platform/frontend/
├── src/
│   ├── components/     # Reusable layout and widget components (Auction, Predictions, Charts)
│   ├── contracts/      # TypeScript interfaces strictly mapped to Backend Pydantic models
│   ├── pages/          # Full page views (Dashboard, TeamAnalytics, Predictions, AuctionRoom)
│   ├── store/          # Zustand global stores (identity, auction, layout state)
│   ├── services/       # Fetch API abstraction clients
│   ├── styles/         # Global styles and Tailwind configurations
│   └── main.tsx        # React mount entrypoint
├── public/             # Static public assets (e.g. fallback background/images)
├── index.html          # HTML frame
└── README.md           # Frontend README
```

---

## 🚀 Running locally

1. Navigate to the frontend directory:
   ```powershell
   cd platform/frontend
   ```
2. Install npm modules:
   ```powershell
   npm install
   ```
3. Run the development server:
   ```powershell
   npm run dev
   ```
   *Open `http://localhost:5173` to access the application.*

4. Validate and build production bundle:
   ```powershell
   npm run build
   ```
   *Compiles code and builds static assets in `dist/` with zero TypeScript errors.*
