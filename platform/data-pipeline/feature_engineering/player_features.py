"""
Player feature engineering for advanced metrics.
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional, Dict, Tuple, Iterable, Set
from datetime import datetime, timedelta
from utils.constants import RECENCY_WEIGHTS, MIN_PLAYER_APPEARANCES, RECENT_MATCH_DAYS

logger = logging.getLogger(__name__)


class PlayerFeatureEngineering:
    """Generate advanced player metrics."""
    
    @staticmethod
    def calculate_per_90_stats(appearances: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
        """Calculate per-90 statistics for players."""
        logger.info("Calculating per-90 statistics...")
        
        # Group by player
        player_stats = appearances.groupby("player_id").agg({
            "goals": "sum",
            "assists": "sum",
            "minutes_played": "sum",
        }).reset_index()
        
        # Calculate per-90
        player_stats["games_played"] = appearances.groupby("player_id").size().values
        player_stats["goals_per_90"] = np.where(
            player_stats["minutes_played"] > 0,
            (player_stats["goals"] / player_stats["minutes_played"]) * 90,
            0
        )
        player_stats["assists_per_90"] = np.where(
            player_stats["minutes_played"] > 0,
            (player_stats["assists"] / player_stats["minutes_played"]) * 90,
            0
        )
        player_stats["contribution_per_90"] = (
            player_stats["goals_per_90"] + player_stats["assists_per_90"]
        )
        
        # Filter minimum appearances
        player_stats = player_stats[player_stats["games_played"] >= MIN_PLAYER_APPEARANCES]
        
        logger.info(f"✓ Calculated per-90 stats for {len(player_stats)} players")
        return player_stats
    
    @staticmethod
    def calculate_consistency_score(appearances: pd.DataFrame) -> Dict[int, float]:
        """Calculate consistency score (goals/assists variance)."""
        logger.info("Calculating consistency scores...")
        
        consistency_scores = {}
        for player_id, group in appearances.groupby("player_id"):
            games = len(group)
            if games < MIN_PLAYER_APPEARANCES:
                continue
            
            goals_data = group["goals"].values
            goals_std = np.std(goals_data) if len(goals_data) > 1 else 0
            goals_mean = np.mean(goals_data)
            
            # Coefficient of variation (lower is more consistent)
            if goals_mean > 0:
                cv = goals_std / goals_mean
                consistency_score = 1 / (1 + cv)  # Normalize to 0-1
            else:
                consistency_score = 1.0 if goals_std == 0 else 0.0
            
            consistency_scores[player_id] = min(consistency_score, 1.0)
        
        logger.info(f"✓ Calculated consistency scores for {len(consistency_scores)} players")
        return consistency_scores
    
    @staticmethod
    def calculate_recent_form(
        appearances: pd.DataFrame,
        cutoff_days: int = RECENT_MATCH_DAYS
    ) -> Dict[int, Tuple[float, float]]:
        """Calculate recent form score (last N days vs all-time)."""
        logger.info(f"Calculating recent form (last {cutoff_days} days)...")
        
        cutoff_date = datetime.now() - timedelta(days=cutoff_days)
        appearances = appearances.copy()
        appearances["date"] = pd.to_datetime(appearances["date"], errors="coerce")

        # All-time aggregates
        all_time = appearances.groupby("player_id").agg(
            total_goals=("goals", "sum"),
            total_minutes=("minutes_played", "sum"),
            total_games=("player_id", "size"),
        )

        # Recent aggregates only on filtered subset
        recent_df = appearances[appearances["date"] >= cutoff_date]
        recent = recent_df.groupby("player_id").agg(
            recent_goals=("goals", "sum"),
            recent_minutes=("minutes_played", "sum"),
            recent_games=("player_id", "size"),
        )

        combined = all_time.join(recent, how="left").fillna(0)
        recent_form_scores = {}

        for player_id, row in combined.iterrows():
            if row["recent_games"] >= MIN_PLAYER_APPEARANCES and row["recent_minutes"] > 0:
                recent_goals_per_90 = (row["recent_goals"] / row["recent_minutes"]) * 90
            else:
                recent_goals_per_90 = 0

            all_time_goals_per_90 = (row["total_goals"] / row["total_minutes"]) * 90 if row["total_minutes"] > 0 else 0

            # Form score: normalize recent to 0-1, capped at 1.0
            recent_score = min(recent_goals_per_90 / max(all_time_goals_per_90, 0.1), 1.0)
            recent_form_scores[player_id] = (recent_score, all_time_goals_per_90)
        
        logger.info(f"✓ Calculated recent form for {len(recent_form_scores)} players")
        return recent_form_scores
    
    @staticmethod
    def calculate_form_score_with_recency(
        recent_form: Dict[int, Tuple[float, float]],
        consistency: Dict[int, float],
        players_2025_26: Optional[Iterable[int]] = None,
        weights: Dict[str, float] = RECENCY_WEIGHTS,
    ) -> Dict[int, float]:
        """Calculate weighted form score with recency bias."""
        logger.info("Calculating weighted form scores with recency bias...")

        players_2025_26_set: Set[int] = set(players_2025_26) if players_2025_26 is not None else set()
        
        form_scores = {}
        for player_id, (recent_score, historical_score) in recent_form.items():
            consistency_score = consistency.get(player_id, 0.5)
            
            # Check if player in 2025-26 data (extra weight if yes)
            bonus = 0.1 if player_id in players_2025_26_set else 0
            
            # Weighted form score
            form_score = (
                weights["recent_2025_26"] * recent_score +
                weights["current_season"] * historical_score * consistency_score +
                weights["historical"] * historical_score
            ) + bonus
            
            form_scores[player_id] = min(form_score, 1.0)
        
        logger.info(f"✓ Calculated weighted form scores for {len(form_scores)} players")
        return form_scores
    
    @staticmethod
    def create_master_players(
        players: pd.DataFrame,
        valuations: pd.DataFrame,
        appearances: pd.DataFrame,
        form_scores: Dict[int, float],
        consistency_scores: Dict[int, float],
    ) -> pd.DataFrame:
        """Create unified master players dataset."""
        logger.info("Creating master players dataset...")
        
        # Start with base player data
        master = players[["player_id", "player_name", "country_of_citizenship", "position", "date_of_birth"]].copy()
        master = master.drop_duplicates(subset=["player_id"])
        
        # Add appearance statistics
        appearance_stats = appearances.groupby("player_id").agg({
            "goals": "sum",
            "assists": "sum",
            "minutes_played": "sum",
        }).reset_index()
        appearance_stats["games_played"] = appearances.groupby("player_id").size().values
        appearance_stats["goals_per_90"] = np.where(
            appearance_stats["minutes_played"] > 0,
            (appearance_stats["goals"] / appearance_stats["minutes_played"]) * 90,
            0
        )
        appearance_stats["assists_per_90"] = np.where(
            appearance_stats["minutes_played"] > 0,
            (appearance_stats["assists"] / appearance_stats["minutes_played"]) * 90,
            0
        )
        
        master = master.merge(appearance_stats, on="player_id", how="left")
        
        # Add latest market value
        latest_valuations = valuations.sort_values("date", ascending=False).drop_duplicates(subset=["player_id"])
        master = master.merge(
            latest_valuations[["player_id", "market_value_in_eur"]],
            on="player_id", how="left"
        )
        master = master.rename(columns={"market_value_in_eur": "market_value"})
        
        # Add engineered features
        master["form_score"] = master["player_id"].map(form_scores).fillna(0.5)
        master["consistency_score"] = master["player_id"].map(consistency_scores).fillna(0.5)
        
        # Calculate contribution per 90
        master["contribution_per_90"] = master["goals_per_90"] + master["assists_per_90"]
        
        # Fill missing numeric values
        numeric_cols = ["goals", "assists", "minutes_played", "games_played", "goals_per_90", "assists_per_90", "contribution_per_90"]
        for col in numeric_cols:
            if col in master.columns:
                master[col] = master[col].fillna(0)
        
        # Fill market value
        master["market_value"] = master["market_value"].fillna(0)
        
        logger.info(f"✓ Created master players dataset: {len(master)} players")
        return master
