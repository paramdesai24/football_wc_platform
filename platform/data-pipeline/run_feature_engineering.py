"""Entrypoint: Run feature engineering for players and countries."""

from utils.logging_utils import setup_logger
from ingestion.loader import DataLoader, save_csv
from feature_engineering.player_features import PlayerFeatureEngineering
from feature_engineering.country_features import CountryFeatureEngineering
from utils.constants import DATASETS
from utils.config import get_processed_paths
import time
import traceback

logger = setup_logger("pipeline", "pipeline.log")


def timed(name: str, fn, *args, **kwargs):
    start = time.time()
    logger.info(f"Starting step: {name}")
    try:
        res = fn(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"Completed step: {name} in {duration:.2f}s")
        return res
    except Exception as e:
        logger.error(f"Step {name} failed: {e}\n{traceback.format_exc()}")
        raise


def main():
    logger.info("Starting feature engineering run...")
    loader = DataLoader(DATASETS)

    # Load datasets with timing
    timed("load_all", loader.load_all)

    # Log dataset sizes
    for k in DATASETS.keys():
        df = loader.get(k)
        if df is None:
            logger.warning(f"Dataset {k} is None after load")
        else:
            logger.info(f"Dataset {k}: {len(df)} rows, {len(df.columns)} columns")

    players = loader.get("players")
    valuations = loader.get("player_valuations")
    appearances = loader.get("appearances")
    results = loader.get("results")
    players_2025_26 = loader.get("players_light_2025_26")
    if players_2025_26 is None:
        players_2025_26 = loader.get("players_full_2025_26")

    pfe = PlayerFeatureEngineering()

    # Run heavy steps with timing and explicit logs
    per90 = timed("calculate_per_90_stats", pfe.calculate_per_90_stats, appearances, players) if appearances is not None and players is not None else None
    consistency = timed("calculate_consistency_score", pfe.calculate_consistency_score, appearances) if appearances is not None else {}
    recent = timed("calculate_recent_form", pfe.calculate_recent_form, appearances) if appearances is not None else {}
    if players_2025_26 is not None:
        bonus_ids = set(players_2025_26["player_id"].dropna().tolist()) if "player_id" in players_2025_26.columns else set()
    else:
        bonus_ids = set()

    form_scores = timed("calculate_form_score_with_recency", pfe.calculate_form_score_with_recency, recent, consistency, bonus_ids) if recent is not None else {}

    cfe = CountryFeatureEngineering()
    country_stats = timed("calculate_country_stats", cfe.calculate_country_stats, results) if results is not None else None
    country_recent = timed("calculate_recent_form_country", cfe.calculate_recent_form_country, results) if results is not None else None

    # Save intermediate outputs
    processed_paths = get_processed_paths()
    out_dir = processed_paths["pipeline_processed"]

    if per90 is not None:
        save_csv(per90, out_dir / "player_per90.csv")
    # Save form_scores and consistency as small CSVs
    if form_scores:
        import pandas as pd
        fs_df = pd.DataFrame(list(form_scores.items()), columns=["player_id", "form_score"]) 
        save_csv(fs_df, out_dir / "player_form_scores.csv")
    if consistency:
        import pandas as pd
        cs_df = pd.DataFrame(list(consistency.items()), columns=["player_id", "consistency_score"]) 
        save_csv(cs_df, out_dir / "player_consistency_scores.csv")

    if country_stats is not None:
        save_csv(country_stats, out_dir / "country_stats.csv")
    if country_recent is not None:
        import pandas as pd
        if isinstance(country_recent, dict):
            country_recent_df = pd.DataFrame(
                [
                    {
                        "country": country,
                        "recent_form_score": values[0] if isinstance(values, tuple) and len(values) > 0 else values,
                        "recent_matches": values[1] if isinstance(values, tuple) and len(values) > 1 else 0,
                    }
                    for country, values in country_recent.items()
                ]
            )
            save_csv(country_recent_df, out_dir / "country_recent_form.csv")
        else:
            save_csv(country_recent, out_dir / "country_recent_form.csv")

    logger.info("Feature engineering run completed")


if __name__ == "__main__":
    main()
