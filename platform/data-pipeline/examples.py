#!/usr/bin/env python3
"""
Quick-start examples for data pipeline usage.

This shows common patterns for using the data pipeline components.
"""

import sys
from pathlib import Path

# Add pipeline to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.constants import DATASETS, OUTPUT_DATASETS
from utils.logging_utils import setup_logger
from ingestion.loader import DataLoader
from audit.auditor import DataAudit
from cleaning.cleaner import DataCleaner
from feature_engineering.player_features import PlayerFeatureEngineering
from feature_engineering.country_features import CountryFeatureEngineering
from exports.database import FootballIntelligenceDB
import pandas as pd

logger = setup_logger(__name__)


def example_load_datasets():
    """Example 1: Load and inspect datasets."""
    logger.info("\n=== Example 1: Load Datasets ===")
    
    loader = DataLoader(DATASETS)
    data = loader.load_all()
    
    for name, df in data.items():
        if df is not None:
            logger.info(f"{name}: {len(df)} rows, {len(df.columns)} columns")


def example_audit_data():
    """Example 2: Audit dataset quality."""
    logger.info("\n=== Example 2: Audit Data ===")
    
    loader = DataLoader(DATASETS)
    data = loader.load_all()
    
    audit = DataAudit()
    report = audit.audit_all(data)
    
    logger.info(f"Audited {len(report)} datasets")
    
    for dataset_name, audit_info in report.items():
        if audit_info:
            logger.info(f"  {dataset_name}:")
            logger.info(f"    - Rows: {audit_info.get('rows', 0)}")
            logger.info(f"    - Columns: {audit_info.get('columns', 0)}")
            if audit_info.get('issues'):
                logger.info(f"    - Issues: {', '.join(audit_info['issues'])}")


def example_clean_data():
    """Example 3: Clean individual datasets."""
    logger.info("\n=== Example 3: Clean Data ===")
    
    loader = DataLoader(DATASETS)
    players_df = loader.load("players")
    
    cleaner = DataCleaner()
    cleaned = cleaner.clean_players(players_df)
    
    logger.info(f"Original: {len(players_df)} rows → Cleaned: {len(cleaned)} rows")


def example_player_features():
    """Example 4: Engineer player features."""
    logger.info("\n=== Example 4: Player Features ===")
    
    loader = DataLoader(DATASETS)
    appearances_df = loader.load("appearances")
    players_df = loader.load("players")
    
    pfe = PlayerFeatureEngineering()
    
    # Calculate per-90 stats
    per_90 = pfe.calculate_per_90_stats(appearances_df, players_df)
    logger.info(f"Calculated per-90 stats for {len(per_90)} players")
    logger.info(f"  Top scorers (goals_per_90):")
    top_scorers = per_90.nlargest(5, "goals_per_90")[["player_id", "goals_per_90"]]
    for idx, row in top_scorers.iterrows():
        logger.info(f"    - Player {row['player_id']}: {row['goals_per_90']:.2f}")


def example_country_features():
    """Example 5: Engineer country features."""
    logger.info("\n=== Example 5: Country Features ===")
    
    loader = DataLoader(DATASETS)
    results_df = loader.load("results")
    
    cfe = CountryFeatureEngineering()
    
    # Calculate country stats
    country_stats = cfe.calculate_country_stats(results_df)
    logger.info(f"Calculated stats for {len(country_stats)} countries")
    logger.info(f"  Top teams (win_rate):")
    top_teams = country_stats.nlargest(5, "win_rate")[["country", "win_rate", "total_matches"]]
    for idx, row in top_teams.iterrows():
        logger.info(f"    - {row['country']}: {row['win_rate']:.2%} ({int(row['total_matches'])} matches)")


def example_database_integration():
    """Example 6: Query database."""
    logger.info("\n=== Example 6: Database Integration ===")
    
    from utils.constants import DATABASE_PATH
    
    db = FootballIntelligenceDB(DATABASE_PATH)
    
    # Query players
    players_df = db.get_players()
    if len(players_df) > 0:
        logger.info(f"Players in database: {len(players_df)}")
        logger.info(f"  Sample:")
        for idx, row in players_df.head(3).iterrows():
            logger.info(f"    - {row['name']} ({row['country']}, {row['position']})")
    else:
        logger.info("No players in database yet. Run pipeline.py first.")
    
    db.close()


def example_export_data():
    """Example 7: Export data to CSV."""
    logger.info("\n=== Example 7: Export Data ===")
    
    from exports.exporter import DataExporter
    
    # Create sample data
    master_players = pd.DataFrame({
        "player_id": [1, 2, 3],
        "name": ["Messi", "Ronaldo", "Neymar"],
        "country": ["Argentina", "Portugal", "Brazil"],
        "position": ["LW", "ST", "LW"],
        "goals_per_90": [0.85, 0.72, 0.68],
    })
    
    output_path = OUTPUT_DATASETS["master_players"]
    exporter = DataExporter()
    success = exporter.export_csv(master_players, output_path, "Sample Players")
    
    if success:
        logger.info(f"✓ Exported to {output_path}")


def main():
    """Run all examples."""
    logger.info("="*80)
    logger.info("PHASE 1 PIPELINE: QUICK-START EXAMPLES")
    logger.info("="*80)
    
    examples = [
        ("Load Datasets", example_load_datasets),
        ("Audit Data", example_audit_data),
        ("Clean Data", example_clean_data),
        ("Player Features", example_player_features),
        ("Country Features", example_country_features),
        ("Database Integration", example_database_integration),
        ("Export Data", example_export_data),
    ]
    
    for name, func in examples:
        try:
            func()
        except Exception as e:
            logger.error(f"Example '{name}' failed: {e}")
    
    logger.info("\n" + "="*80)
    logger.info("Examples completed!")
    logger.info("="*80)


if __name__ == "__main__":
    main()
