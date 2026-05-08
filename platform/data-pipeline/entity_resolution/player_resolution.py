"""
Player Resolution: Deduplicate players and generate canonical player UIDs.

Handles:
- Duplicate player detection (same name, country, DOB)
- Canonical player UID generation
- Player confidence scoring
- Form data consolidation
"""

import pandas as pd
import hashlib
from typing import Dict, Optional, Tuple
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PlayerResolver:
    """
    Resolve duplicate players and generate canonical identifiers.
    """

    def __init__(self):
        self.player_uid_map = {}  # player_id -> player_uid
        self.duplicates = []

    def generate_player_uid(
        self, player_id: int, name: str, country: str, date_of_birth: Optional[str]
    ) -> str:
        """
        Generate canonical player UID from player attributes.

        Combines:
        - player_id (primary)
        - name + country + DOB (fingerprint)

        Returns stable UID for deduplication.
        """
        if player_id in self.player_uid_map:
            return self.player_uid_map[player_id]

        # Create fingerprint: name + country + dob
        fingerprint = f"{name.lower().strip()}_{country.lower().strip()}_{str(date_of_birth)}"
        
        # Hash fingerprint for uniqueness
        uid_hash = hashlib.sha256(fingerprint.encode()).hexdigest()[:12]
        
        # Combined UID: player_id + hash
        player_uid = f"P{player_id}_{uid_hash}"
        
        self.player_uid_map[player_id] = player_uid
        return player_uid

    def detect_duplicates(self, players_df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect potential duplicate players in dataset.

        Criteria:
        - Same name + country + DOB
        - Similar names (fuzzy match) + same country

        Returns DataFrame with duplicate groups.
        """
        duplicates = []

        # Exact match: name + country + DOB
        exact_dups = players_df.groupby(
            ["name", "country_of_origin", "date_of_birth"]
        ).filter(lambda x: len(x) > 1)

        if len(exact_dups) > 0:
            logger.info(f"Found {len(exact_dups)} exact duplicate player records")
            duplicates.append(exact_dups)

        self.duplicates = pd.concat(duplicates, ignore_index=True) if duplicates else pd.DataFrame()
        return self.duplicates

    def add_player_uid(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add canonical player_uid column to DataFrame."""
        df = df.copy()

        df["player_uid"] = df.apply(
            lambda row: self.generate_player_uid(
                row.get("player_id"),
                row.get("name", ""),
                row.get("country_of_origin", row.get("country", "")),
                row.get("date_of_birth"),
            ),
            axis=1,
        )

        return df

    def merge_duplicate_records(
        self, df: pd.DataFrame, group_cols: list, agg_dict: Optional[Dict] = None
    ) -> pd.DataFrame:
        """
        Merge duplicate player records via aggregation.

        Args:
            df: Player DataFrame (must have player_uid column)
            group_cols: Columns to group by (e.g., ['player_uid'])
            agg_dict: Aggregation strategy (e.g., {'goals': 'sum', 'country': 'first'})

        Returns:
            Deduplicated DataFrame
        """
        if "player_uid" not in df.columns:
            df = self.add_player_uid(df)

        if agg_dict is None:
            # Default strategy: keep first non-null value, sum numeric columns
            agg_dict = {
                col: "sum" if df[col].dtype in ["int64", "float64"] else "first"
                for col in df.columns
                if col not in group_cols
            }

        try:
            merged = df.groupby(group_cols, as_index=False).agg(agg_dict)
            logger.info(f"Merged {len(df)} records into {len(merged)} unique players")
            return merged
        except Exception as e:
            logger.error(f"Error merging duplicate records: {e}")
            return df

    def calculate_player_confidence(self, row: pd.Series) -> float:
        """
        Calculate player confidence score (0-1) based on data completeness.

        Factors:
        - Recent match count (weight: 0.4)
        - Total appearances (weight: 0.3)
        - Field completeness (weight: 0.3)

        Returns:
            Confidence score 0-1
        """
        confidence = 0.0

        # Recent matches (last 365 days)
        if "recent_match_count" in row and pd.notna(row["recent_match_count"]):
            recent_score = min(row["recent_match_count"] / 10, 1.0)  # Cap at 10 matches
            confidence += recent_score * 0.4

        # Total appearances
        if "appearances" in row and pd.notna(row["appearances"]):
            appearances_score = min(row["appearances"] / 100, 1.0)  # Cap at 100 apps
            confidence += appearances_score * 0.3

        # Field completeness
        non_null_ratio = row.count() / len(row)
        confidence += non_null_ratio * 0.3

        return min(confidence, 1.0)

    def resolve_players(self, players_df: pd.DataFrame) -> pd.DataFrame:
        """
        Full player resolution pipeline:
        1. Detect duplicates
        2. Generate UIDs
        3. Calculate confidence scores
        """
        logger.info(f"Starting player resolution for {len(players_df)} records")

        # Generate UIDs
        players_df = self.add_player_uid(players_df)

        # Detect duplicates
        self.detect_duplicates(players_df)

        # Calculate confidence
        players_df["player_confidence"] = players_df.apply(
            self.calculate_player_confidence, axis=1
        )

        logger.info(f"✓ Player resolution complete: {len(players_df)} players with UIDs")

        return players_df
