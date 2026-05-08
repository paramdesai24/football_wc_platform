"""
Schema Registry: Centralized dtype definitions and CSV loading utilities.

Handles:
- Explicit dtype definitions for all 15 datasets
- Mixed-type column handling (numeric + strings)
- Standardized NA value detection
- Safe CSV loading with validation
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, List, Any
import logging

logger = logging.getLogger(__name__)

# ============================================================================
# STANDARDIZED NA VALUES
# ============================================================================

STANDARD_NA_VALUES = ["N/A", "NULL", "null", "-", "", "unknown", "Unknown", "nan", "NaN", "NAN", "None"]

# ============================================================================
# SCHEMA DEFINITIONS FOR ALL TRANSFER MARKET DATASETS
# ============================================================================

TRANSFER_MARKET_SCHEMAS = {
    "players": {
        "player_id": "int64",
        "name": "string",
        "country_of_origin": "string",
        "date_of_birth": "string",
        "country": "string",
        "club": "string",
        "contract_expires": "string",
        "last_contract_update": "string",
        "player_url": "string",
        "current_club": "string",
        "player_code": "string",
        "highest_market_value": "string",
        "image_url": "string",
    },
    "valuations": {
        "player_id": "int64",
        "name": "string",
        "country": "string",
        "club": "string",
        "position": "string",
        "date_of_birth": "string",
        "contract_expires": "string",
        "market_value_in_eur": "float64",
        "n_transfers": "float64",
        "last_season": "string",
        "scouted_by": "string",
    },
    "clubs": {
        "club_id": "int64",
        "name": "string",
        "country_id": "int64",
        "country": "string",
        "city": "string",
        "url": "string",
        "type": "string",
        "founded_year": "float64",
        "address": "string",
        "phone": "string",
        "fax": "string",
        "email": "string",
        "website": "string",
    },
    "competitions": {
        "competition_id": "int64",
        "name": "string",
        "type": "string",
        "country_id": "int64",
        "country": "string",
        "confederation": "string",
        "url": "string",
    },
    "countries": {
        "country_id": "int64",
        "name": "string",
        "confederation": "string",
        "iso": "string",
        "iso3": "string",
        "map_colors": "string",
        "url": "string",
    },
    "games": {
        "game_id": "int64",
        "competition_id": "int64",
        "season": "float64",
        "round": "string",
        "date": "string",
        "home_club_id": "int64",
        "away_club_id": "int64",
        "home_club_goals": "float64",
        "away_club_goals": "float64",
        "aggregate_goals": "string",
        "competition_type": "string",
    },
    "game_lineups": {
        "game_id": "int64",
        "player_id": "int64",
        "player_club_id": "int64",
        "player_position": "string",
        "player_current_club_id": "int64",
        "player_shirt_number": "float64",
        "is_captain": "int64",
        "assumed_lineup": "int64",
    },
    "game_events": {
        "game_id": "int64",
        "player_id": "int64",
        "player_club_id": "int64",
        "type": "string",
        "minute": "float64",
        "player_in_id": "float64",
        "player_assist_id": "float64",
    },
    "appearances": {
        "appearance_id": "int64",
        "game_id": "int64",
        "player_id": "int64",
        "player_club_id": "int64",
        "player_position": "string",
        "player_current_club_id": "int64",
        "player_shirt_number": "float64",
        "is_captain": "int64",
        "minutes_played": "float64",
        "goals": "float64",
        "assists": "float64",
        "date": "string",
        "player_name": "string",
        "player_country": "string",
        "competition_type": "string",
        "season": "float64",
    },
    "player_valuations": {
        "player_id": "int64",
        "date": "string",
        "market_value_in_eur": "float64",
        "player_club_id": "int64",
        "player_contract_expires": "string",
    },
    "transfers": {
        "transfer_id": "int64",
        "player_id": "int64",
        "player_name": "string",
        "player_country": "string",
        "player_position": "string",
        "player_current_club_id": "int64",
        "player_club_domestic_competition_id": "int64",
        "date": "string",
        "transfer_type": "string",
        "from_club_id": "int64",
        "to_club_id": "int64",
        "transfer_fee": "string",
        "season": "float64",
    },
    "national_teams": {
        "team_id": "int64",
        "name": "string",
        "country_id": "int64",
        "confederation": "string",
        "url": "string",
    },
    "club_games": {
        "game_id": "int64",
        "club_id": "int64",
        "season": "float64",
        "date": "string",
        "home_club_id": "int64",
        "away_club_id": "int64",
        "home_goals": "float64",
        "away_goals": "float64",
        "goals_for": "float64",
        "goals_against": "float64",
    },
}

# ============================================================================
# INTERNATIONAL RESULTS SCHEMAS
# ============================================================================

INTL_RESULTS_SCHEMAS = {
    "results": {
        "date": "string",
        "home_team": "string",
        "away_team": "string",
        "home_score": "int64",
        "away_score": "int64",
        "tournament": "string",
        "city": "string",
        "country": "string",
        "neutral": "int64",
    },
    "goalscorers": {
        "date": "string",
        "home_team": "string",
        "away_team": "string",
        "team": "string",
        "scorer": "string",
        "minute": "string",
        "penalty": "int64",
        "own_goal": "int64",
        "tournament": "string",
    },
    "shootouts": {
        "date": "string",
        "home_team": "string",
        "away_team": "string",
        "winner": "string",
        "tournament": "string",
    },
    "former_names": {
        "country_code": "string",
        "former_name": "string",
        "year_start": "float64",
        "year_end": "float64",
    },
}

# ============================================================================
# COMBINED SCHEMA REGISTRY
# ============================================================================

SCHEMA_REGISTRY = {
    **TRANSFER_MARKET_SCHEMAS,
    **INTL_RESULTS_SCHEMAS,
}


class SchemaLoader:
    """
    Centralized schema-aware CSV loader with validation and type coercion.
    """

    def __init__(self):
        self.loaded_schemas = {}
        self.warnings = []

    def load_csv(
        self,
        filepath: Path,
        dataset_name: Optional[str] = None,
        force_schema: bool = True,
        validate_schema: bool = True,
    ) -> pd.DataFrame:
        """
        Load CSV with schema validation and type coercion.

        Args:
            filepath: Path to CSV file
            dataset_name: Name of dataset (if None, inferred from filename)
            force_schema: If True, coerce to schema types
            validate_schema: If True, validate after loading

        Returns:
            DataFrame with proper types
        """
        filepath = Path(filepath)

        if not dataset_name:
            dataset_name = filepath.stem.replace("cleaned_", "")

        logger.debug(f"Loading {dataset_name} from {filepath}")

        try:
            # Attempt schema-guided loading
            schema = SCHEMA_REGISTRY.get(dataset_name, {})

            if schema and force_schema:
                df = pd.read_csv(
                    filepath,
                    dtype=schema,
                    na_values=STANDARD_NA_VALUES,
                    low_memory=False,
                    keep_default_na=True,
                )
            else:
                df = pd.read_csv(
                    filepath,
                    na_values=STANDARD_NA_VALUES,
                    low_memory=False,
                    keep_default_na=True,
                )

            if validate_schema:
                self._validate_schema(df, dataset_name, schema)

            self.loaded_schemas[dataset_name] = schema
            logger.info(f"✓ Loaded {dataset_name}: {df.shape[0]} rows × {df.shape[1]} columns")

            return df

        except Exception as e:
            logger.error(f"Error loading {dataset_name}: {e}")
            raise

    def _validate_schema(self, df: pd.DataFrame, dataset_name: str, schema: Dict[str, str]):
        """Validate loaded DataFrame against schema."""
        if not schema:
            return

        for col in schema:
            if col not in df.columns:
                logger.warning(f"[{dataset_name}] Missing expected column: {col}")

    def coerce_types(self, df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
        """Coerce DataFrame columns to schema types."""
        schema = SCHEMA_REGISTRY.get(dataset_name, {})

        if not schema:
            return df

        for col, dtype in schema.items():
            if col in df.columns:
                try:
                    if dtype == "string":
                        df[col] = df[col].astype("string")
                    elif dtype == "int64":
                        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
                    elif dtype == "float64":
                        df[col] = pd.to_numeric(df[col], errors="coerce")
                except Exception as e:
                    logger.warning(f"Could not coerce {col} to {dtype}: {e}")

        return df

    def get_schema(self, dataset_name: str) -> Dict[str, str]:
        """Get schema definition for dataset."""
        return SCHEMA_REGISTRY.get(dataset_name, {})


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_schema_loader = SchemaLoader()


def load_dataset(filepath: Path, dataset_name: Optional[str] = None) -> pd.DataFrame:
    """Load dataset with centralized schema."""
    return _schema_loader.load_csv(filepath, dataset_name)


def get_schema(dataset_name: str) -> Dict[str, str]:
    """Get schema for dataset."""
    return _schema_loader.get_schema(dataset_name)
