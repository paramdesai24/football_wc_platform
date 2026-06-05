import asyncio
import logging
import os
import time
from datetime import datetime, timedelta
from app.core.database import PostgresSessionLocal
from app.services.match_scraper import SCRAPER_STATUS

logger = logging.getLogger(__name__)


async def start_match_scraper_cron():
    logger.info("Starting background match scraper cron")

    while True:
        # Read environment variable dynamically at start of loop to allow run-time changes
        interval_hours = float(os.getenv("SCRAPER_INTERVAL_HOURS", "24"))
        interval_seconds = int(interval_hours * 3600)
        logger.info(f"[SCRAPER] Interval read: {interval_hours} hours ({interval_seconds}s)")

        start_time = time.time()
        # Calculate next run timestamp
        next_run = datetime.utcnow() + timedelta(seconds=interval_seconds)
        SCRAPER_STATUS["next_scheduled_run"] = next_run.isoformat() + "Z"
        SCRAPER_STATUS["status"] = "running"
        SCRAPER_STATUS["error_message"] = None

        logger.info("scraper started")

        try:
            if PostgresSessionLocal is not None:
                async with PostgresSessionLocal() as db:
                    from app.api.v1.endpoints.match_admin import scrape_and_process
                    result = await scrape_and_process(db)

                    duration = time.time() - start_time

                    # Structured logs mapping exactly to requested tags
                    logger.info(f"fixtures found: {result.get('fixtures_found', 0)}")
                    logger.info(f"fixtures skipped: {result.get('fixtures_skipped', 0)}")
                    logger.info(f"fixtures processed: {result.get('fixtures_processed', 0)}")
                    logger.info(f"player records updated: {result.get('players_processed', 0)}")
                    logger.info(f"API failures: {result.get('api_failures', 0)}")
                    logger.info(f"run duration: {duration:.2f}s")

                    # Update status tracking
                    SCRAPER_STATUS["last_successful_run"] = datetime.utcnow().isoformat() + "Z"
                    SCRAPER_STATUS["fixtures_processed_in_last_run"] = result.get("fixtures_processed", 0)
                    SCRAPER_STATUS["players_processed_in_last_run"] = result.get("players_processed", 0)
                    
                    from sqlalchemy import func
                    from sqlalchemy.future import select
                    from app.models.auction_models import WCMatch, PlayerPerformance
                    matches_count = await db.scalar(
                        select(func.count()).select_from(WCMatch).where(WCMatch.status == "completed")
                    )
                    perf_count = await db.scalar(
                        select(func.count()).select_from(PlayerPerformance)
                    )
                    SCRAPER_STATUS["total_fixtures_processed"] = matches_count or 0
                    SCRAPER_STATUS["total_players_processed"] = perf_count or 0
                    SCRAPER_STATUS["status"] = "success"
            else:
                logger.warning("[SCRAPER] PostgresSessionLocal is not configured. Skipping background scrape.")
                SCRAPER_STATUS["status"] = "failed"
                SCRAPER_STATUS["error_message"] = "PostgresSessionLocal not configured"
        except asyncio.CancelledError:
            logger.info("Background match scraper task was cancelled.")
            raise
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"[SCRAPER] Error during background match scraper execution: {e}", exc_info=True)
            logger.info("API failures: 1")
            logger.info(f"run duration: {duration:.2f}s")

            SCRAPER_STATUS["status"] = "failed"
            SCRAPER_STATUS["error_message"] = str(e)

        logger.info(f"[SCRAPER] Sleeping for {interval_seconds} seconds until next scheduled run at {SCRAPER_STATUS['next_scheduled_run']}.")
        await asyncio.sleep(interval_seconds)
