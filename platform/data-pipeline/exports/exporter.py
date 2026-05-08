"""
Data export utilities for processed datasets.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Optional
from utils.constants import OUTPUT_DATASETS

logger = logging.getLogger(__name__)


class DataExporter:
    """Export processed datasets to CSV and database."""
    
    @staticmethod
    def export_csv(df: pd.DataFrame, output_path: Path, name: str) -> bool:
        """Export DataFrame to CSV."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            logger.info(f"✓ Exported {name}: {len(df)} rows to {output_path.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to export {name} to CSV: {e}")
            return False
    
    @staticmethod
    def export_all_datasets(
        master_players: pd.DataFrame,
        master_countries: pd.DataFrame,
        player_form: pd.DataFrame,
        country_strength: pd.DataFrame,
        squad_aggregates: pd.DataFrame,
    ) -> dict:
        """Export all datasets to CSV files."""
        logger.info("Exporting all datasets to CSV...")
        
        results = {}
        
        results["master_players"] = DataExporter.export_csv(
            master_players,
            OUTPUT_DATASETS["master_players"],
            "Master Players"
        )
        
        results["master_countries"] = DataExporter.export_csv(
            master_countries,
            OUTPUT_DATASETS["master_countries"],
            "Master Countries"
        )
        
        results["player_form"] = DataExporter.export_csv(
            player_form,
            OUTPUT_DATASETS["player_form"],
            "Player Form"
        )
        
        results["country_strength"] = DataExporter.export_csv(
            country_strength,
            OUTPUT_DATASETS["country_strength"],
            "Country Strength"
        )
        
        results["squad_aggregates"] = DataExporter.export_csv(
            squad_aggregates,
            OUTPUT_DATASETS["squad_aggregates"],
            "Squad Aggregates"
        )
        
        logger.info(f"✓ Exported {sum(results.values())} datasets")
        return results
