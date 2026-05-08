"""Entrypoint: Run cleaning pipelines and save cleaned datasets."""

from utils.logging_utils import setup_logger
from ingestion.loader import DataLoader
from cleaning.cleaner import DataCleaner
from utils.constants import DATASETS, OUTPUT_DATASETS, PROCESSED_DATA_DIR
from utils.config import get_processed_paths
from ingestion.loader import save_csv

logger = setup_logger("pipeline", "pipeline.log")


def main():
    logger.info("Starting cleaning run...")
    loader = DataLoader(DATASETS)
    loader.load_all()

    cleaner = DataCleaner()

    players = loader.get("players")
    valuations = loader.get("player_valuations")
    appearances = loader.get("appearances")
    games = loader.get("games")
    results = loader.get("results")
    clubs = loader.get("clubs")

    cleaned_players = cleaner.clean_players(players) if players is not None else None
    cleaned_valuations = cleaner.clean_valuations(valuations) if valuations is not None else None
    cleaned_appearances = cleaner.clean_appearances(appearances) if appearances is not None else None
    cleaned_games = cleaner.clean_games(games) if games is not None else None
    cleaned_results = cleaner.clean_results(results) if results is not None else None
    cleaned_clubs = cleaner.clean_clubs(clubs) if clubs is not None else None

    # Save cleaned artifacts to pipeline processed dir
    processed_paths = get_processed_paths()
    out_dir = processed_paths["pipeline_processed"]

    if cleaned_players is not None:
        save_csv(cleaned_players, out_dir / "cleaned_players.csv")
    if cleaned_valuations is not None:
        save_csv(cleaned_valuations, out_dir / "cleaned_valuations.csv")
    if cleaned_appearances is not None:
        save_csv(cleaned_appearances, out_dir / "cleaned_appearances.csv")
    if cleaned_games is not None:
        save_csv(cleaned_games, out_dir / "cleaned_games.csv")
    if cleaned_results is not None:
        save_csv(cleaned_results, out_dir / "cleaned_results.csv")
    if cleaned_clubs is not None:
        save_csv(cleaned_clubs, out_dir / "cleaned_clubs.csv")

    logger.info("Cleaning run completed")


if __name__ == "__main__":
    main()
