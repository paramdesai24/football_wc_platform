"""
Group Stage Simulation Engine
================================
Simulates all group-stage matches using the Phase 3 match prediction engine.
Updates standings after each matchday.
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional
from scipy.stats import poisson

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))

from match_engine.probabilities.match_probability import MatchProbabilityEngine
from ..utils.team_state import apply_team_state, soft_cap_goals, update_team_state
from ..utils.constants import (
    POINTS_WIN, POINTS_DRAW, POINTS_LOSS,
    HOST_CONFEDERATION, HOST_CONTINENT_XG_BOOST,
    TEAM_NAME_ALIASES,
)

logger = logging.getLogger("tournament.group_stage")


class GroupStageEngine:
    """
    Simulates group-stage matches using the Phase 3 prediction engine.

    For each match:
    1. Calls MatchProbabilityEngine for xG predictions
    2. Applies host-continent boost if applicable
    3. Samples goals from Poisson(xG) for stochastic outcomes
    4. Returns match result with full metadata
    """

    def __init__(self, prediction_engine: Optional[MatchProbabilityEngine] = None,
                 stochastic: bool = True, seed: Optional[int] = None):
        """
        Args:
            prediction_engine: Phase 3 prediction engine (auto-created if None)
            stochastic: If True, sample goals from Poisson. If False, use xG directly.
            seed: Random seed for reproducibility.
        """
        self._engine = prediction_engine or MatchProbabilityEngine()
        self._stochastic = stochastic
        self._rng = np.random.default_rng(seed)

    def resolve_team_name(self, name: str) -> str:
        """Resolve tournament team names to Phase 2 data names."""
        return TEAM_NAME_ALIASES.get(name, name)

    def simulate_match(self, home_team: str, away_team: str,
                       group: str = "", matchday: int = 0,
                       match_id: str = "",
                       team_state: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Simulate a single group-stage match.

        Returns:
            Dict with home_goals, away_goals, home_xg, away_xg,
            result, points, and prediction metadata.
        """
        # Resolve names for prediction engine
        h_resolved = self.resolve_team_name(home_team)
        a_resolved = self.resolve_team_name(away_team)

        # Get prediction from Phase 3 engine
        try:
            home_data = self._engine._loader.get_team(h_resolved)
            away_data = self._engine._loader.get_team(a_resolved)
            if home_data is None or away_data is None:
                raise ValueError(f"Missing team data for {home_team} vs {away_team}")

            home_snapshot = apply_team_state(home_data, team_state.get(home_team) if team_state else None)
            away_snapshot = apply_team_state(away_data, team_state.get(away_team) if team_state else None)

            prediction = self._engine.predict(
                h_resolved, a_resolved,
                venue="neutral",  # World Cup = neutral venues
                tournament="world_cup_group",
                home_data=home_snapshot,
                away_data=away_snapshot,
            )
        except ValueError as e:
            logger.warning("Prediction failed for %s vs %s: %s", home_team, away_team, e)
            # Fallback: even match
            prediction = {
                "home_xg": 1.2, "away_xg": 1.2,
                "home_win_prob": 0.35, "draw_prob": 0.30, "away_win_prob": 0.35,
            }

        home_xg = prediction.get("home_xg", 1.2)
        away_xg = prediction.get("away_xg", 1.2)

        # Apply host-continent boost
        home_conf = self._get_confederation(home_team)
        away_conf = self._get_confederation(away_team)

        if home_conf == HOST_CONFEDERATION:
            home_xg += HOST_CONTINENT_XG_BOOST
        if away_conf == HOST_CONFEDERATION:
            away_xg += HOST_CONTINENT_XG_BOOST

        # Generate scoreline
        if self._stochastic:
            home_goals = int(self._rng.poisson(max(home_xg, 0.1)))
            away_goals = int(self._rng.poisson(max(away_xg, 0.1)))
            # Soft cap to suppress absurd blowouts without flattening variance.
            home_goals = soft_cap_goals(min(home_goals, 8), "group")
            away_goals = soft_cap_goals(min(away_goals, 8), "group")
        else:
            # Deterministic: use rounded xG
            home_goals = round(home_xg)
            away_goals = round(away_xg)

        # Determine result and points
        if home_goals > away_goals:
            result = "home_win"
            home_pts, away_pts = POINTS_WIN, POINTS_LOSS
        elif away_goals > home_goals:
            result = "away_win"
            home_pts, away_pts = POINTS_LOSS, POINTS_WIN
        else:
            result = "draw"
            home_pts, away_pts = POINTS_DRAW, POINTS_DRAW

        home_snapshot_state = team_state.get(home_team) if team_state else None
        away_snapshot_state = team_state.get(away_team) if team_state else None
        update_team_state(home_snapshot_state, home_goals, away_goals, "group")
        update_team_state(away_snapshot_state, away_goals, home_goals, "group")

        return {
            "match_id": match_id,
            "group": group,
            "matchday": matchday,
            "home_team": home_team,
            "away_team": away_team,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "home_xg": round(home_xg, 2),
            "away_xg": round(away_xg, 2),
            "result": result,
            "home_points": home_pts,
            "away_points": away_pts,
            "home_win_prob": prediction.get("home_win_prob", 0.33),
            "draw_prob": prediction.get("draw_prob", 0.33),
            "away_win_prob": prediction.get("away_win_prob", 0.33),
            "stage": "group",
        }

    def simulate_matchday(self, fixtures: List[Dict], matchday: int) -> List[Dict]:
        """Simulate all matches for a given matchday."""
        md_fixtures = [f for f in fixtures if f["matchday"] == matchday]
        results = []
        for fix in md_fixtures:
            result = self.simulate_match(
                home_team=fix["home_team"],
                away_team=fix["away_team"],
                group=fix["group"],
                matchday=matchday,
                match_id=fix["match_id"],
                team_state=getattr(self, "_team_state", None),
            )
            results.append(result)
            logger.info(
                "  %s %d-%d %s (Group %s, MD%d)",
                result["home_team"], result["home_goals"],
                result["away_goals"], result["away_team"],
                result["group"], matchday,
            )
        return results

    def simulate_all_group_matches(self, fixtures: List[Dict]) -> List[Dict]:
        """Simulate all group-stage matches across all matchdays."""
        all_results = []
        for md in range(1, 4):
            logger.info("=== Matchday %d ===", md)
            results = self.simulate_matchday(fixtures, md)
            all_results.extend(results)
        return all_results

    def _get_confederation(self, team_name: str) -> str:
        """Get confederation for a team (for host-continent boost)."""
        try:
            team_data = self._engine._loader.get_team(
                self.resolve_team_name(team_name).lower()
            )
            if team_data:
                return team_data.get("confederation", "")
        except Exception:
            pass
        return ""
