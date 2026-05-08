"""
Club Resolution: Deduplicate clubs and resolve naming inconsistencies.

Handles:
- Club name canonicalization
- Canonical club UID generation
- Club alias resolution
- Country assignment for clubs
"""

import pandas as pd
import hashlib
from typing import Dict, Optional
import logging
from utils.entity_registry import canonicalize_club, canonicalize_country

logger = logging.getLogger(__name__)


class ClubResolver:
    """
    Resolve club entities and generate canonical identifiers.
    """

    def __init__(self):
        self.club_uid_map = {}  # club_id -> club_uid
        self.club_canonical_map = {}  # club_name -> canonical_name

    def generate_club_uid(self, club_id: int, club_name: str) -> str:
        """
        Generate canonical club UID.

        Args:
            club_id: Transfer market club ID
            club_name: Club name

        Returns:
            Stable club UID (e.g., CL_349)
        """
        if club_id in self.club_uid_map:
            return self.club_uid_map[club_id]

        # Use club_id as primary identifier
        club_uid = f"CL_{club_id}"
        self.club_uid_map[club_id] = club_uid
        
        return club_uid

    def add_club_uid(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add canonical club_uid column to DataFrame.

        Assumes 'club_id' column exists.
        """
        df = df.copy()

        if "club_id" not in df.columns:
            logger.warning("No club_id column found")
            return df

        club_name_col = "name" if "name" in df.columns else "club"

        df["club_uid"] = df.apply(
            lambda row: self.generate_club_uid(
                row["club_id"],
                row.get(club_name_col, "")
            ),
            axis=1,
        )

        return df

    def canonicalize_clubs(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Canonicalize club names in DataFrame.

        Applies mapping to 'club', 'name', 'from_club', 'to_club' columns.
        """
        df = df.copy()

        club_columns = [col for col in df.columns if "club" in col.lower() or col == "name"]

        for col in club_columns:
            if df[col].dtype == "object":
                df[col] = df[col].apply(canonicalize_club)

        return df

    def deduplicate_clubs(self, clubs_df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate club records based on club_id or name.
        """
        if "club_id" in clubs_df.columns:
            deduplicated = clubs_df.drop_duplicates(subset=["club_id"], keep="first")
        elif "name" in clubs_df.columns:
            deduplicated = clubs_df.drop_duplicates(subset=["name"], keep="first")
        else:
            deduplicated = clubs_df.drop_duplicates(keep="first")

        logger.info(f"Deduplicated clubs: {len(clubs_df)} → {len(deduplicated)}")

        return deduplicated

    def add_club_country(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add club country assignment if not present.
        """
        df = df.copy()

        if "country" not in df.columns:
            # Try to infer from club data or leave null
            if "country_id" in df.columns:
                # Could map country_id to country, but skip for now
                df["country"] = None
            else:
                df["country"] = None

        return df

    def resolve_clubs(self, clubs_df: pd.DataFrame) -> pd.DataFrame:
        """
        Full club resolution pipeline:
        1. Canonicalize names
        2. Generate UIDs
        3. Deduplicate
        4. Add country
        """
        logger.info(f"Starting club resolution for {len(clubs_df)} records")

        # Canonicalize
        clubs_df = self.canonicalize_clubs(clubs_df)

        # Generate UIDs
        clubs_df = self.add_club_uid(clubs_df)

        # Deduplicate
        clubs_df = self.deduplicate_clubs(clubs_df)

        # Add country
        clubs_df = self.add_club_country(clubs_df)

        logger.info(f"✓ Club resolution complete: {len(clubs_df)} clubs with UIDs")

        return clubs_df
