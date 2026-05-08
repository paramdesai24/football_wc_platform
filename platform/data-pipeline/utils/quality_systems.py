"""
Data Quality Systems: Confidence scoring, fallback hierarchies, quality tiering, and feature lineage.

Handles:
- Confidence score calculation (0-1)
- Multi-tier form fallback system (5 levels)
- Hierarchical country estimation (confederation fallbacks)
- Data quality tiering (Tier 1-3)
- Reliability weighting (metric + confidence pairs)
- Feature lineage tracking (source + transformations)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIDENCE SCORING SYSTEM
# ============================================================================

class ConfidenceScorer:
    """
    Calculate confidence scores for player records (0-1 scale).

    Confidence based on:
    - Match count
    - Minutes played
    - Recency (recent data weights more)
    - Data completeness
    """

    @staticmethod
    def calculate_player_confidence(
        appearances: int,
        minutes_played: float,
        recent_match_count: int,
        days_since_last_match: int,
        field_completeness: float,
    ) -> float:
        """
        Calculate player confidence score.

        Args:
            appearances: Total international appearances
            minutes_played: Total minutes played
            recent_match_count: Matches in last 365 days
            days_since_last_match: Days since last competitive match
            field_completeness: Ratio of non-null fields (0-1)

        Returns:
            Confidence score (0-1)
        """
        confidence = 0.0

        # Recent match frequency (weight: 0.35)
        recent_score = min(recent_match_count / 8.0, 1.0)  # 8+ recent = full score
        confidence += recent_score * 0.35

        # Total experience (weight: 0.25)
        experience_score = min(appearances / 50.0, 1.0)  # 50+ apps = full score
        confidence += experience_score * 0.25

        # Minutes played (weight: 0.15)
        minutes_score = min(minutes_played / 3600.0, 1.0)  # 3600+ mins = full score
        confidence += minutes_score * 0.15

        # Recency (weight: 0.15)
        # Full score if recent, decay over time
        if days_since_last_match <= 30:
            recency_score = 1.0
        elif days_since_last_match <= 90:
            recency_score = 0.8
        elif days_since_last_match <= 180:
            recency_score = 0.6
        elif days_since_last_match <= 365:
            recency_score = 0.4
        else:
            recency_score = 0.1
        confidence += recency_score * 0.15

        # Field completeness (weight: 0.10)
        confidence += field_completeness * 0.10

        return min(confidence, 1.0)

    @staticmethod
    def add_confidence_scores(df: pd.DataFrame) -> pd.DataFrame:
        """Add confidence_score column to DataFrame."""
        df = df.copy()

        if "appearances" not in df.columns:
            df["appearances"] = 0
        if "minutes_played" not in df.columns:
            df["minutes_played"] = 0.0
        if "recent_match_count" not in df.columns:
            df["recent_match_count"] = 0
        if "days_since_last_match" not in df.columns:
            df["days_since_last_match"] = 9999

        df["confidence_score"] = df.apply(
            lambda row: ConfidenceScorer.calculate_player_confidence(
                appearances=int(row.get("appearances", 0)),
                minutes_played=float(row.get("minutes_played", 0)),
                recent_match_count=int(row.get("recent_match_count", 0)),
                days_since_last_match=int(row.get("days_since_last_match", 9999)),
                field_completeness=row.count() / len(row),
            ),
            axis=1,
        )

        return df


# ============================================================================
# FORM FALLBACK HIERARCHY (5-TIER)
# ============================================================================

class FormFallbackSystem:
    """
    Multi-tier form scoring fallback system to handle sparse data.

    Hierarchy:
    1. Recent 5 matches
    2. Current season (if available)
    3. Last 2 years
    4. Historical average
    5. Country average (confederation fallback)
    """

    @staticmethod
    def get_recent_form_score(appearances_df: pd.DataFrame, player_id: int, days_back: int = 30) -> Optional[float]:
        """Get form from recent N days."""
        if player_id not in appearances_df["player_id"].values:
            return None

        player_apps = appearances_df[appearances_df["player_id"] == player_id]
        if len(player_apps) == 0:
            return None

        recent = player_apps[player_apps["days_since_match"] <= days_back]
        if len(recent) == 0:
            return None

        # Form = average goals/assists per recent match
        goals = recent["goals"].sum()
        assists = recent["assists"].sum()
        matches = len(recent)

        return (goals * 0.6 + assists * 0.4) / matches if matches > 0 else None

    @staticmethod
    def get_seasonal_form_score(appearances_df: pd.DataFrame, player_id: int, season: int) -> Optional[float]:
        """Get form from specific season."""
        player_apps = appearances_df[appearances_df["player_id"] == player_id]
        seasonal = player_apps[player_apps["season"] == season]

        if len(seasonal) == 0:
            return None

        goals = seasonal["goals"].sum()
        assists = seasonal["assists"].sum()
        matches = len(seasonal)

        return (goals * 0.6 + assists * 0.4) / matches if matches > 0 else None

    @staticmethod
    def get_historical_average(appearances_df: pd.DataFrame, player_id: int) -> Optional[float]:
        """Get career average form."""
        player_apps = appearances_df[appearances_df["player_id"] == player_id]

        if len(player_apps) == 0:
            return None

        goals = player_apps["goals"].sum()
        assists = player_apps["assists"].sum()
        matches = len(player_apps)

        return (goals * 0.6 + assists * 0.4) / matches if matches > 0 else None

    @staticmethod
    def get_country_average_form(appearances_df: pd.DataFrame, country: str) -> Optional[float]:
        """Get country squad average form."""
        country_apps = appearances_df[appearances_df["country"] == country]

        if len(country_apps) == 0:
            return None

        goals = country_apps["goals"].sum()
        assists = country_apps["assists"].sum()
        matches = len(country_apps)

        return (goals * 0.6 + assists * 0.4) / matches if matches > 0 else None

    @staticmethod
    def apply_form_fallback_hierarchy(
        form_score: Optional[float],
        appearances_df: pd.DataFrame,
        player_id: int,
        country: str,
        current_season: int,
    ) -> Tuple[float, int]:
        """
        Apply 5-tier fallback hierarchy.

        Returns:
            (form_score, fallback_tier)
            tier 0: original score
            tier 1: recent matches
            tier 2: seasonal
            tier 3: historical
            tier 4: country average
            tier 5: default 0.5
        """
        # Tier 0: Original score
        if pd.notna(form_score) and form_score > 0:
            return (form_score, 0)

        # Tier 1: Recent 5 matches
        recent = FormFallbackSystem.get_recent_form_score(appearances_df, player_id)
        if recent is not None:
            return (recent, 1)

        # Tier 2: Current season
        seasonal = FormFallbackSystem.get_seasonal_form_score(appearances_df, player_id, current_season)
        if seasonal is not None:
            return (seasonal, 2)

        # Tier 3: Historical average
        historical = FormFallbackSystem.get_historical_average(appearances_df, player_id)
        if historical is not None:
            return (historical, 3)

        # Tier 4: Country average
        country_avg = FormFallbackSystem.get_country_average_form(appearances_df, country)
        if country_avg is not None:
            return (country_avg, 4)

        # Tier 5: Default neutral form
        return (0.5, 5)


# ============================================================================
# HIERARCHICAL COUNTRY ESTIMATION
# ============================================================================

class CountryEstimationSystem:
    """
    Hierarchical estimation for countries with sparse data.

    Fallback:
    1. Direct country stats
    2. Confederation average
    3. Squad market value
    4. Player club strength
    """

    @staticmethod
    def estimate_country_rating(
        country: str,
        direct_rating: Optional[float],
        confederation_avg: Optional[float],
        squad_market_value: Optional[float],
        confederation: str,
    ) -> Tuple[float, int, str]:
        """
        Estimate country rating with fallback system.

        Returns:
            (rating, estimation_tier, estimation_method)
        """
        # Tier 1: Direct stats
        if pd.notna(direct_rating) and direct_rating > 0:
            return (direct_rating, 1, "direct_stats")

        # Tier 2: Confederation average
        if pd.notna(confederation_avg) and confederation_avg > 0:
            return (confederation_avg, 2, "confederation_average")

        # Tier 3: Squad market value (proxy for strength)
        if pd.notna(squad_market_value):
            # Normalize market value to 0-100 scale
            # Assume avg squad value = €500M, scale accordingly
            normalized = min(squad_market_value / 500e6 * 75, 100)
            if normalized > 0:
                return (normalized, 3, "squad_valuation")

        # Tier 4: Default confederation rating
        default_confederation_rating = {
            "UEFA": 78,
            "CONMEBOL": 76,
            "AFC": 70,
            "CAF": 65,
            "CONCACAF": 68,
            "OFC": 60,
        }
        default = default_confederation_rating.get(confederation, 60)
        return (default, 4, "confederation_default")


# ============================================================================
# DATA QUALITY TIERING
# ============================================================================

class DataQualityTier:
    """
    Assign data quality tier (1-3) based on completeness and confidence.

    Tier 1: High confidence (confidence > 0.85, completeness > 90%)
    Tier 2: Moderate confidence (0.50 < confidence ≤ 0.85, 60-90% completeness)
    Tier 3: Low confidence (confidence ≤ 0.50 or completeness < 60%)
    """

    @staticmethod
    def assign_tier(confidence_score: float, completeness: float) -> int:
        """
        Assign quality tier.

        Args:
            confidence_score: 0-1
            completeness: 0-1 (ratio of non-null fields)

        Returns:
            Tier (1, 2, or 3)
        """
        if confidence_score > 0.85 and completeness > 0.90:
            return 1
        elif confidence_score > 0.50 and completeness > 0.60:
            return 2
        else:
            return 3

    @staticmethod
    def add_data_quality_tier(df: pd.DataFrame) -> pd.DataFrame:
        """Add data_quality_tier column."""
        df = df.copy()

        if "confidence_score" not in df.columns:
            df["confidence_score"] = 0.5

        completeness = df.apply(lambda row: row.count() / len(row), axis=1)

        df["data_quality_tier"] = df.apply(
            lambda row: DataQualityTier.assign_tier(
                row["confidence_score"], completeness.loc[row.name]
            ),
            axis=1,
        )

        return df


# ============================================================================
# RELIABILITY WEIGHTING
# ============================================================================

class ReliabilityWeighting:
    """
    Attach reliability scores to key metrics.

    Each metric has an associated confidence value.
    """

    @staticmethod
    def add_metric_reliability(df: pd.DataFrame, metric_col: str, confidence_col: str) -> pd.DataFrame:
        """
        Create reliability pair: metric + confidence.

        Args:
            df: DataFrame
            metric_col: Column name for metric value
            confidence_col: Column name for metric confidence

        Returns:
            DataFrame with new columns:
            - {metric_col}_value
            - {metric_col}_confidence
        """
        df = df.copy()

        df[f"{metric_col}_value"] = df[metric_col]
        df[f"{metric_col}_confidence"] = df[confidence_col]

        return df

    @staticmethod
    def apply_reliability_weighting(df: pd.DataFrame, metrics: List[str]) -> pd.DataFrame:
        """
        Apply reliability weighting to multiple metrics.

        Args:
            df: DataFrame
            metrics: List of metric column names

        Returns:
            DataFrame with weighted metrics
        """
        df = df.copy()

        for metric in metrics:
            if metric in df.columns and "confidence_score" in df.columns:
                df = ReliabilityWeighting.add_metric_reliability(
                    df, metric, "confidence_score"
                )

        return df


# ============================================================================
# FEATURE LINEAGE TRACKING
# ============================================================================

class FeatureLineageTracker:
    """
    Track source dataset and transformation steps for each feature.

    Enables debugging, transparency, and ML explainability.
    """

    def __init__(self):
        self.lineage: Dict[str, Dict] = {}
        self.transformation_steps: List[Dict] = []

    def record_source(self, feature_name: str, source_dataset: str, source_columns: List[str]):
        """Record feature source."""
        self.lineage[feature_name] = {
            "source_dataset": source_dataset,
            "source_columns": source_columns,
            "transformations": [],
            "created_at": datetime.now().isoformat(),
        }

    def record_transformation(
        self, feature_name: str, transformation_type: str, parameters: Dict = None
    ):
        """Record transformation applied to feature."""
        if feature_name not in self.lineage:
            self.lineage[feature_name] = {"transformations": [], "created_at": datetime.now().isoformat()}

        self.lineage[feature_name]["transformations"].append({
            "type": transformation_type,
            "parameters": parameters or {},
            "timestamp": datetime.now().isoformat(),
        })

    def record_aggregation(
        self, output_feature: str, input_features: List[str], method: str
    ):
        """Record feature aggregation."""
        self.record_transformation(
            output_feature,
            "aggregation",
            {
                "input_features": input_features,
                "method": method,
            },
        )

    def export_lineage(self, filepath: Path) -> None:
        """Export feature lineage to JSON."""
        with open(filepath, "w") as f:
            json.dump(self.lineage, f, indent=2)

        logger.info(f"✓ Feature lineage exported to {filepath}")

    def get_lineage_report(self) -> str:
        """Generate human-readable lineage report."""
        report = "FEATURE LINEAGE REPORT\n"
        report += "=" * 50 + "\n\n"

        for feature, metadata in self.lineage.items():
            report += f"Feature: {feature}\n"
            report += f"  Source: {metadata.get('source_dataset', 'unknown')}\n"
            report += f"  Columns: {metadata.get('source_columns', [])}\n"

            if metadata.get("transformations"):
                report += "  Transformations:\n"
                for i, trans in enumerate(metadata["transformations"], 1):
                    report += f"    {i}. {trans['type']}\n"
                    if trans.get("parameters"):
                        for key, val in trans["parameters"].items():
                            report += f"       - {key}: {val}\n"

            report += "\n"

        return report


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_lineage_tracker = FeatureLineageTracker()


def get_lineage_tracker() -> FeatureLineageTracker:
    """Get global feature lineage tracker."""
    return _lineage_tracker
