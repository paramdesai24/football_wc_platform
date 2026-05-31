CHUNK 8 — Admin match entry + final wiring

Run order and instructions

1. Set up Supabase project and copy connection string into `platform/backend-api/.env` as `SUPABASE_POSTGRES_URL`.

2. Data pipeline: build auction players

   cd platform/data-pipeline
   python build_auction_players.py

   Expect output: "Loaded ~2300 players to auction_players table"

3. Run Alembic migrations

   cd platform/backend-api
   alembic upgrade head

4. Create indexes in Supabase SQL Editor (paste the CREATE INDEX statements from Chunk 2)

5. Start backend

   cd platform/backend-api
   uvicorn app.main:app --reload

6. Install frontend websocket dependency

   cd platform/frontend
   npm install react-use-websocket

7. Start frontend

   npm run dev

8. Test flow (manual): create league → join → start auction → nominate → bid → verify `squads` table

Notes:
- Frontend env: create `platform/frontend/.env.local` containing `VITE_API_BASE_URL` and `VITE_WS_BASE_URL` if desired. Example in `platform/frontend/.env.example`.
- Backend env example at `platform/backend-api/.env.example`.
