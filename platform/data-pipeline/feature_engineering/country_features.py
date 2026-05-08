"""
Country feature engineering and team aggregation.
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from utils.constants import RECENT_MATCH_DAYS, CONFEDERATIONS, TOP_COMPETITIONS

logger = logging.getLogger(__name__)


class CountryFeatureEngineering:
    """Generate country-level metrics."""
    
    @staticmethod
    def calculate_country_stats(results: pd.DataFrame) -> pd.DataFrame:
        """Calculate country-level statistics from match results."""
        logger.info("Calculating country statistics...")
        
        country_stats = []
        
        for country in pd.concat([results["home_team"], results["away_team"]]).unique():
            if pd.isna(country):
                continue
            
            home_matches = results[results["home_team"] == country]
            away_matches = results[results["away_team"] == country]
            
            # Home stats
            home_wins = (home_matches["home_score"] > home_matches["away_score"]).sum()
            home_losses = (home_matches["home_score"] < home_matches["away_score"]).sum()
            home_draws = (home_matches["home_score"] == home_matches["away_score"]).sum()
            home_goals = home_matches["home_score"].sum()
            home_conceded = home_matches["away_score"].sum()
            
            # Away stats
            away_wins = (away_matches["away_score"] > away_matches["home_score"]).sum()
            away_losses = (away_matches["away_score"] < away_matches["home_score"]).sum()
            away_draws = (away_matches["away_score"] == away_matches["home_score"]).sum()
            away_goals = away_matches["away_score"].sum()
            away_conceded = away_matches["home_score"].sum()
            
            # Total stats
            total_wins = home_wins + away_wins
            total_losses = home_losses + away_losses
            total_draws = home_draws + away_draws
            total_matches = total_wins + total_losses + total_draws
            total_goals = home_goals + away_goals
            total_conceded = home_conceded + away_conceded
            
            if total_matches > 0:
                win_rate = total_wins / total_matches
                goals_per_match = total_goals / total_matches
                conceded_per_match = total_conceded / total_matches
            else:
                win_rate = goals_per_match = conceded_per_match = 0
            
            country_stats.append({
                "country": country,
                "total_matches": total_matches,
                "wins": total_wins,
                "draws": total_draws,
                "losses": total_losses,
                "win_rate": win_rate,
                "goals_for": total_goals,
                "goals_against": total_conceded,
                "goals_per_match": goals_per_match,
                "conceded_per_match": conceded_per_match,
                "goal_differential": total_goals - total_conceded,
            })
        
        df = pd.DataFrame(country_stats)
        logger.info(f"✓ Calculated stats for {len(df)} countries")
        return df
    
    @staticmethod
    def calculate_recent_form_country(
        results: pd.DataFrame,
        cutoff_days: int = RECENT_MATCH_DAYS,
    ) -> Dict[str, Tuple[float, int]]:
        """Calculate recent form for countries."""
        logger.info(f"Calculating country recent form (last {cutoff_days} days)...")
        
        cutoff_date = datetime.now() - timedelta(days=cutoff_days)
        results["date"] = pd.to_datetime(results["date"], errors="coerce")
        
        recent_matches = results[results["date"] >= cutoff_date]
        
        form_scores = {}
        for country in pd.concat([recent_matches["home_team"], recent_matches["away_team"]]).unique():
            if pd.isna(country):
                continue
            
            home = recent_matches[recent_matches["home_team"] == country]
            away = recent_matches[recent_matches["away_team"] == country]
            
            home_points = (home["home_score"] > home["away_score"]).sum() * 3 + (home["home_score"] == home["away_score"]).sum()
            away_points = (away["away_score"] > away["home_score"]).sum() * 3 + (away["away_score"] == away["home_score"]).sum()
            
            total_matches = len(home) + len(away)
            total_points = home_points + away_points
            
            form_score = (total_points / (total_matches * 3)) if total_matches > 0 else 0.5
            form_scores[country] = (form_score, total_matches)
        
        logger.info(f"✓ Calculated recent form for {len(form_scores)} countries")
        return form_scores
    
    @staticmethod
    def create_master_countries(
        country_stats: pd.DataFrame,
        recent_form: Dict[str, Tuple[float, int]],
        national_teams: Optional[pd.DataFrame] = None,
    ) -> pd.DataFrame:
        """Create master countries dataset."""
        logger.info("Creating master countries dataset...")
        
        master = country_stats.copy()
        
        # Add recent form
        master["recent_form_score"] = master["country"].map(lambda c: recent_form.get(c, (0.5, 0))[0]).fillna(0.5)
        master["recent_matches"] = master["country"].map(lambda c: recent_form.get(c, (0.5, 0))[1]).fillna(0)
        
        # Calculate attack and defense ratings
        master["attack_rating"] = (master["goals_per_match"] / max(master["goals_per_match"].max(), 1)) * 100
        master["defense_rating"] = (1 - (master["conceded_per_match"] / max(master["conceded_per_match"].max(), 1))) * 100
        
        # Calculate historical strength (wins + form)
        master["historical_strength"] = (
            (master["win_rate"] * 0.5) +
            (master["recent_form_score"] * 0.5)
        ) * 100
        
        # Add confederation if available
        if national_teams is not None and "confederation" in national_teams.columns:
            national_teams_dict = dict(zip(national_teams["name"], national_teams.get("confederation", "")))
            master["confederation"] = master["country"].map(national_teams_dict)
        
        logger.info(f"✓ Created master countries dataset: {len(master)} countries")
        return master
    
    @staticmethod
    def calculate_squad_aggregates(
        master_players: pd.DataFrame,
    ) -> pd.DataFrame:
        """Calculate team/squad aggregates."""
        logger.info("Calculating squad aggregates...")
        
        squad_agg = master_players.groupby("country").agg({
            "player_id": "count",
            "market_value": ["sum", "mean"],
            "goals_per_90": "mean",
            "assists_per_90": "mean",
            "form_score": "mean",
            "consistency_score": "mean",
        }).reset_index()
        
        squad_agg.columns = [
            "country",
            "squad_size",
            "total_market_value",
            "avg_player_value",
            "avg_goals_per_90",
            "avg_assists_per_90",
            "avg_form_score",
            "avg_consistency_score",
        ]
        
        # Calculate composite squad rating
        squad_agg["squad_strength"] = (
            (squad_agg["avg_goals_per_90"] / max(squad_agg["avg_goals_per_90"].max(), 1)) * 30 +
            (squad_agg["avg_form_score"] * 40) +
            (squad_agg["avg_consistency_score"] * 30)
        )
        
        logger.info(f"✓ Calculated squad aggregates for {len(squad_agg)} countries")
        return squad_agg
