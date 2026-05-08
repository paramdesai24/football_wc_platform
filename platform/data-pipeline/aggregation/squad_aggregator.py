"""Aggregate player metrics into squad-level composites."""

import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class SquadAggregator:
    """Aggregate player-level metrics into squad-level metrics."""

    @staticmethod
    def aggregate(master_players: pd.DataFrame) -> pd.DataFrame:
        """Return squad aggregates grouped by country."""
        if master_players is None or master_players.empty:
            logger.warning("No master players provided to SquadAggregator")
            return pd.DataFrame()

        logger.info("Aggregating squad metrics by country...")

        country_col = "country_of_citizenship" if "country_of_citizenship" in master_players.columns else "country"
        if country_col not in master_players.columns:
            logger.warning("No country column available for squad aggregation")
            return pd.DataFrame()

        working = master_players.copy()
        for column in ["market_value", "goals_per_90", "assists_per_90", "form_score", "consistency_score"]:
            if column not in working.columns:
                working[column] = 0

        grp = working.groupby(country_col)

        squads = grp.agg(
            squad_size=("player_id", "nunique"),
            total_market_value=("market_value", "sum"),
            avg_player_value=("market_value", "mean"),
            avg_goals_per_90=("goals_per_90", "mean"),
            avg_assists_per_90=("assists_per_90", "mean"),
            avg_form_score=("form_score", "mean"),
            avg_consistency_score=("consistency_score", "mean"),
        ).reset_index().rename(columns={country_col: "country"})

        # Composite squad strength (normalized 0-1)
        # Simple heuristic: weighted sum of avg_form_score (0.5), avg_goals_per_90 (0.3), avg_consistency_score (0.2)
        squads["squad_strength"] = (
            0.5 * squads["avg_form_score"].fillna(0) +
            0.3 * squads["avg_goals_per_90"].fillna(0) +
            0.2 * squads["avg_consistency_score"].fillna(0)
        )

        logger.info(f"✓ Aggregated {len(squads)} squads")
        return squads
