"""
Competition Resolution: Standardize competitions and resolve naming inconsistencies.

Handles:
- Competition name canonicalization
- Canonical competition UID generation
- Competition type assignment
- Competition tier classification
"""

import pandas as pd
from typing import Dict, Optional
import logging
from utils.entity_registry import canonicalize_competition

logger = logging.getLogger(__name__)

# Competition tier classification
COMPETITION_TIER_MAP = {
    "UEFA Champions League": 1,  # Top tier: continental club competitions
    "UEFA Europa League": 2,
    "European Super Cup": 2,
    "UEFA Conference League": 3,
    "Premier League": 1,  # Top tier: domestic elite
    "La Liga": 1,
    "Serie A": 1,
    "Bundesliga": 1,
    "Ligue 1": 1,
    "Eredivisie": 2,  # Tier 2: strong domestic
    "Belgian First Division": 2,
    "Portuguese Liga": 2,
    "Primeira Liga": 2,
    "Serie B": 3,  # Tier 3: second division
    "Championship": 3,
    "Ligue 2": 3,
    "2. Bundesliga": 3,
    "Bundesliga II": 3,
    "FIFA World Cup": 1,  # International tier 1: world championships
    "UEFA European Championship": 1,
    "Copa América": 1,
    "Africa Cup of Nations": 2,  # International tier 2: continental
    "AFC Asian Cup": 2,
    "CONCACAF Championship": 2,
    "Gold Cup": 2,
}


class CompetitionResolver:
    """
    Resolve competition entities and generate canonical identifiers.
    """

    def __init__(self):
        self.competition_uid_map = {}  # competition_id -> competition_uid

    def generate_competition_uid(self, competition_id: int, competition_name: str) -> str:
        """
        Generate canonical competition UID.

        Args:
            competition_id: Transfer market competition ID
            competition_name: Competition name

        Returns:
            Stable competition UID (e.g., CO_1)
        """
        if competition_id in self.competition_uid_map:
            return self.competition_uid_map[competition_id]

        # Use competition_id as primary identifier
        competition_uid = f"CO_{competition_id}"
        self.competition_uid_map[competition_id] = competition_uid
        
        return competition_uid

    def add_competition_uid(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add canonical competition_uid column to DataFrame.

        Assumes 'competition_id' column exists.
        """
        df = df.copy()

        if "competition_id" not in df.columns:
            logger.warning("No competition_id column found")
            return df

        competition_name_col = "name" if "name" in df.columns else "competition"

        df["competition_uid"] = df.apply(
            lambda row: self.generate_competition_uid(
                int(row["competition_id"]),
                row.get(competition_name_col, "")
            ),
            axis=1,
        )

        return df

    def canonicalize_competitions(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Canonicalize competition names in DataFrame.

        Applies mapping to 'competition', 'tournament', 'type' columns.
        """
        df = df.copy()

        comp_columns = [
            col for col in df.columns 
            if "competition" in col.lower() or "tournament" in col.lower()
        ]

        for col in comp_columns:
            if df[col].dtype == "object":
                df[col] = df[col].apply(canonicalize_competition)

        return df

    def add_competition_tier(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Assign competition tier (1=elite, 2=strong, 3=secondary).

        Used for weighting metrics by competition quality.
        """
        df = df.copy()

        comp_col = None
        for col in ["name", "competition", "tournament", "type"]:
            if col in df.columns:
                comp_col = col
                break

        if not comp_col:
            logger.warning("No competition column found for tier assignment")
            return df

        df["competition_tier"] = df[comp_col].apply(
            lambda x: COMPETITION_TIER_MAP.get(x, 3) if pd.notna(x) else 3
        )

        return df

    def deduplicate_competitions(self, competitions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate competition records based on competition_id or name.
        """
        if "competition_id" in competitions_df.columns:
            deduplicated = competitions_df.drop_duplicates(
                subset=["competition_id"], keep="first"
            )
        elif "name" in competitions_df.columns:
            deduplicated = competitions_df.drop_duplicates(
                subset=["name"], keep="first"
            )
        else:
            deduplicated = competitions_df.drop_duplicates(keep="first")

        logger.info(f"Deduplicated competitions: {len(competitions_df)} → {len(deduplicated)}")

        return deduplicated

    def resolve_competitions(self, competitions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Full competition resolution pipeline:
        1. Canonicalize names
        2. Generate UIDs
        3. Add tier
        4. Deduplicate
        """
        logger.info(f"Starting competition resolution for {len(competitions_df)} records")

        # Canonicalize
        competitions_df = self.canonicalize_competitions(competitions_df)

        # Generate UIDs
        competitions_df = self.add_competition_uid(competitions_df)

        # Add tier
        competitions_df = self.add_competition_tier(competitions_df)

        # Deduplicate
        competitions_df = self.deduplicate_competitions(competitions_df)

        logger.info(f"✓ Competition resolution complete: {len(competitions_df)} competitions with UIDs")

        return competitions_df
