"""Entrypoint: Export processed datasets to CSV and SQLite database."""

from pathlib import Path
import logging
import shutil

import pandas as pd

from exports.database import FootballIntelligenceDB
from exports.exporter import DataExporter
from utils.config import get_processed_paths
from utils.constants import DATABASE_PATH, OUTPUT_DATASETS
from utils.logging_utils import setup_logger

logger = setup_logger("pipeline", "pipeline.log")


def main():
    logger.info("Starting export run...")

    processed_paths = get_processed_paths()
    pipeline_dir = processed_paths["pipeline_processed"]
    project_dir = processed_paths["project_processed"]

    def read_first_existing(*filenames: str) -> pd.DataFrame:
        for filename in filenames:
            path = pipeline_dir / filename
            if path.exists():
                try:
                    return pd.read_csv(path)
                except Exception:
                    continue
        return pd.DataFrame()

    # Prefer the engineered master files if they exist; otherwise fall back to staged intermediates.
    master_players = read_first_existing("master_players.csv", "cleaned_players.csv")
    master_countries = read_first_existing("master_countries.csv", "country_aggregates.csv", "country_stats.csv")
    
    # Consolidate master_countries by country_uid to eliminate duplicates
    if not master_countries.empty and "country_uid" in master_countries.columns:
        def agg_func(series):
            if series.dtype == 'object' or series.dtype == 'string':
                # For strings, take the first non-null value
                return series.dropna().iloc[0] if not series.dropna().empty else None
            else:
                # For numeric, take the mean
                numeric = pd.to_numeric(series, errors='coerce')
                return numeric.mean() if not numeric.isna().all() else None
        
        master_countries = master_countries.groupby("country_uid", as_index=False).agg(agg_func)
        logger.info(f"Consolidated master_countries to {len(master_countries)} unique countries by country_uid")

    form_base = read_first_existing("player_form.csv", "player_per90.csv")
    player_form_scores = read_first_existing("player_form_scores.csv")
    player_consistency_scores = read_first_existing("player_consistency_scores.csv")

    if form_base.empty and not master_players.empty:
        preferred_columns = [
            "player_id",
            "player_uid",
            "country_uid",
            "club_uid",
            "form_score",
            "form_score_value",
            "form_score_confidence",
            "confidence_score",
            "data_quality_tier",
            "consistency_score",
            "contribution_per_90",
            "impact_score",
            "impact_score_confidence",
        ]
        available_columns = [column for column in preferred_columns if column in master_players.columns]
        form_base = master_players[available_columns].copy()

    if not form_base.empty and not player_form_scores.empty and "player_id" in form_base.columns and "player_id" in player_form_scores.columns:
        player_form = form_base.merge(player_form_scores, on="player_id", how="left")
    else:
        player_form = form_base

    if not player_form.empty and not player_consistency_scores.empty and "player_id" in player_form.columns and "player_id" in player_consistency_scores.columns:
        player_form = player_form.merge(player_consistency_scores, on="player_id", how="left")

    country_strength = read_first_existing("country_strength.csv", "country_stats.csv")
    squad_aggregates = read_first_existing("squad_aggregates.csv", "country_aggregates.csv")

    exporter = DataExporter()
    results = exporter.export_all_datasets(
        master_players if master_players is not None else pd.DataFrame(),
        master_countries if master_countries is not None else pd.DataFrame(),
        player_form if player_form is not None else pd.DataFrame(),
        country_strength if country_strength is not None else pd.DataFrame(),
        squad_aggregates if squad_aggregates is not None else pd.DataFrame(),
    )

    # Copy outputs only when source and target folders differ.
    try:
        if pipeline_dir.resolve() == project_dir.resolve():
            logger.info("Processed source and target are identical; skipping compatibility copy")
        else:
            project_dir.mkdir(parents=True, exist_ok=True)
            for f in pipeline_dir.glob("*"):
                if not f.is_file():
                    continue
                if f.suffix.lower() not in {".csv", ".json"}:
                    continue
                target = project_dir / f.name
                if f.resolve() == target.resolve():
                    continue
                shutil.copy2(f, target)
            logger.info(f"Copied processed artifacts to {project_dir}")
    except Exception as e:
        logger.error(f"Failed to copy processed CSVs: {e}")

    # Ensure SQLite DB exists and insert tables
    try:
        db = FootballIntelligenceDB(DATABASE_PATH)
        db.create_tables()
        if master_players is not None and not master_players.empty:
            db.insert_master_players(master_players)
            db.insert_players(master_players)
        if master_countries is not None and not master_countries.empty:
            db.insert_master_countries(master_countries)
            db.insert_countries(master_countries)
        if player_form is not None and not player_form.empty:
            db.insert_player_form(player_form)
        if country_strength is not None and not country_strength.empty:
            db.insert_country_strength(country_strength)
        if squad_aggregates is not None and not squad_aggregates.empty:
            db.insert_squad_aggregates(squad_aggregates)
        db.close()
        logger.info(f"SQLite database created/updated at {DATABASE_PATH}")
    except Exception as e:
        logger.error(f"Database export failed: {e}")

    logger.info("Export run completed")


if __name__ == "__main__":
    main()
