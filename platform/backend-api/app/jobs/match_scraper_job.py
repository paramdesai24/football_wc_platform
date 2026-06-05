import asyncio
import logging
from app.core.database import PostgresSessionLocal

logger = logging.getLogger(__name__)


async def start_match_scraper_cron(interval_seconds: int = 3 * 24 * 60 * 60):
    logger.info(f"Starting background match scraper cron (interval: {interval_seconds}s)")
    while True:
        try:
            logger.info("Executing background match scraper...")
            if PostgresSessionLocal is not None:
                async with PostgresSessionLocal() as db:
                    from app.api.v1.endpoints.match_admin import scrape_and_process
                    result = await scrape_and_process(db)
                    logger.info(f"Background match scraper complete: {result}")
            else:
                logger.warning("PostgresSessionLocal is not configured. Skipping background scrape.")
        except asyncio.CancelledError:
            logger.info("Background match scraper task was cancelled.")
            raise
        except Exception as e:
            logger.error(f"Error during background match scraper execution: {e}", exc_info=True)
        
        logger.info(f"Sleeping for {interval_seconds} seconds until next scrape.")
        await asyncio.sleep(interval_seconds)
