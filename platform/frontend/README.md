# Platform Frontend — React + TypeScript (Vite)

This folder contains the single-page application for the FIFA WC simulation platform.

Core technologies

- React, TypeScript
- Vite (dev server + build)
- CSS variables + global styles in `src/styles/globals.css`

Quickstart (development)

```powershell
Set-Location "C:\FIFA WC\platform\frontend"
npm install
npm run dev
```

Build for production

```powershell
Set-Location "C:\FIFA WC\platform\frontend"
npm run build
```

Environment

- `VITE_API_BASE_URL` — base URL for backend API (default: `http://127.0.0.1:8000`)

Structure highlights

- `src/pages/` — top-level pages (TournamentPage, PlayAsTeamPage, RankingsPage, etc.)
- `src/components/` — reusable UI components (tables, flags, cards)
- `src/contracts/` — TypeScript interfaces shared between UI and backend payloads
- `src/services/api.ts` — API helpers and endpoint wrappers

Notes

- The frontend unwraps backend payloads that are returned in a `{ data: ... }` envelope — ensure your endpoints follow the expected response shape or adjust the unwrap helpers in `src/services/api.ts`.
- Tournament UI uses a quick-refresh path to request a small number of simulations for responsive UX. See `src/pages/TournamentPage.tsx` for the constant used.

If you want more developer tips or architecture diagrams, update this file or `PROJECT_STATUS.md`.
