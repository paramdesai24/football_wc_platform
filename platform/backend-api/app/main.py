from fastapi import FastAPI
from fastapi import WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os

from app.core.config import settings
from app.core.database import PostgresSessionLocal, init_db
from app.core.logging import setup_logging
from app.api.v1.router import api_router
from app.api.v1.endpoints import health
from app.services.auction_ws import handle_connection

logger = logging.getLogger(__name__)
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.PROJECT_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    os.makedirs(os.path.join(os.path.dirname(os.path.dirname(__file__)), "data"), exist_ok=True)
    init_db()
    logger.info("Database initialized")
    
    # Initialize Postgres tables for auction/FPL
    from app.core.database import postgres_engine
    from app.models.auction_models import AuctionBase
    if postgres_engine is not None:
        try:
            from sqlalchemy import text
            async with postgres_engine.begin() as conn:
                await conn.run_sync(AuctionBase.metadata.create_all)
                await conn.execute(text("ALTER TABLE league_members ADD COLUMN IF NOT EXISTS is_disqualified BOOLEAN DEFAULT FALSE;"))
                await conn.execute(text("ALTER TABLE player_performances ADD COLUMN IF NOT EXISTS goals_conceded INTEGER DEFAULT 0;"))
                await conn.execute(text("ALTER TABLE player_performances ADD COLUMN IF NOT EXISTS penalties_scored INTEGER DEFAULT 0;"))
                await conn.execute(text("ALTER TABLE player_performances ADD COLUMN IF NOT EXISTS penalties_missed INTEGER DEFAULT 0;"))
                await conn.execute(text("ALTER TABLE player_performances ADD COLUMN IF NOT EXISTS penalties_saved INTEGER DEFAULT 0;"))
                await conn.execute(text("ALTER TABLE player_performances ADD COLUMN IF NOT EXISTS player_rating FLOAT;"))
            logger.info("Postgres tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Postgres tables: {e}")
            
    # Start the background scraper task (executes every 3 days)
    import asyncio
    from app.jobs.match_scraper_job import start_match_scraper_cron
    scraper_task = asyncio.create_task(start_match_scraper_cron())

    yield

    logger.info("Shutting down")
    # Cancel the background scraper task on shutdown
    scraper_task.cancel()
    try:
        await scraper_task
    except asyncio.CancelledError:
        logger.info("Background scraper task cancelled successfully during shutdown.")



def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:5173",
            "https://fc-analytics.vercel.app",
        ],
        allow_origin_regex=r"https://.*\.vercel\.app",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, tags=["Health"])
    app.include_router(api_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()


@app.websocket("/ws/auction/{league_id}")
async def auction_websocket(
    websocket: WebSocket,
    league_id: str,
    user_id: str,
    username: str,
):
    await websocket.accept()
    if PostgresSessionLocal is None:
        await websocket.close(code=1011)
        return

    async with PostgresSessionLocal() as db:
        await handle_connection(league_id, user_id, username, websocket, db)
