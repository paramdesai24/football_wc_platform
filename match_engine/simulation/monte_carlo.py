"""
Monte Carlo Match Simulation Engine
=====================================
Simulates individual matches thousands of times using Poisson-sampled
goals to generate robust probabilistic outcomes including upset
detection and variance analysis.
"""

import logging
import numpy as np
from typing import Dict, Any, Optional

from ..utils.constants import DEFAULT_SIMULATIONS, MAX_SIMULATIONS, SIMULATION_SEED
from ..utils.helpers import clamp

logger = logging.getLogger("match_engine.monte_carlo")


class MonteCarloSimulator:
    """
    Monte Carlo match simulation using Poisson goal sampling.
    
    For each simulation:
    1. Sample home goals from Poisson(home_xg)
    2. Sample away goals from Poisson(away_xg)
    3. Determine outcome
    4. Aggregate over N simulations
    """

    def __init__(self, n_simulations: int = DEFAULT_SIMULATIONS, seed: int = SIMULATION_SEED):
        self.n_simulations = min(n_simulations, MAX_SIMULATIONS)
        self.rng = np.random.default_rng(seed)

    def simulate_match(
        self,
        home_xg: float,
        away_xg: float,
        home_name: str = "Home",
        away_name: str = "Away",
        n: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Simulate a match N times and aggregate results.

        Returns
        -------
        dict with win/draw/loss percentages, average scores,
        upset probability, score distribution, and variance metrics
        """
        n_sims = n or self.n_simulations

        # Sample goals using Poisson distribution with soft goal cap
        # Reduces extreme scorelines (5+ goal wins) to ~2-3% probability
        home_goals = self.rng.poisson(lam=max(home_xg, 0.1), size=n_sims)
        away_goals = self.rng.poisson(lam=max(away_xg, 0.1), size=n_sims)
        
        # Apply soft goal cap: 5+ goals are capped at 4 with 30% probability
        # This prevents absurd 6-0, 7-1 scorelines while maintaining randomness
        high_goal_mask_h = home_goals >= 5
        high_goal_mask_a = away_goals >= 5
        if np.any(high_goal_mask_h):
            cap_applied_h = self.rng.uniform(size=np.sum(high_goal_mask_h)) < 0.30
            home_goals[high_goal_mask_h] = np.where(
                cap_applied_h, 4, home_goals[high_goal_mask_h]
            )
        if np.any(high_goal_mask_a):
            cap_applied_a = self.rng.uniform(size=np.sum(high_goal_mask_a)) < 0.30
            away_goals[high_goal_mask_a] = np.where(
                cap_applied_a, 4, away_goals[high_goal_mask_a]
            )

        # Outcomes
        home_wins = int(np.sum(home_goals > away_goals))
        draws = int(np.sum(home_goals == away_goals))
        away_wins = int(np.sum(home_goals < away_goals))

        # Score statistics
        avg_home = float(np.mean(home_goals))
        avg_away = float(np.mean(away_goals))
        std_home = float(np.std(home_goals))
        std_away = float(np.std(away_goals))

        # Most common scoreline
        scores = list(zip(home_goals.tolist(), away_goals.tolist()))
        from collections import Counter
        score_counts = Counter(scores)
        most_common = score_counts.most_common(5)

        # Upset detection: the team with lower xG wins
        if home_xg > away_xg:
            upset_pct = away_wins / n_sims
            favorite = home_name
        elif away_xg > home_xg:
            upset_pct = home_wins / n_sims
            favorite = away_name
        else:
            upset_pct = 0.0
            favorite = "Even"

        return {
            "home_team": home_name,
            "away_team": away_name,
            "simulations": n_sims,
            "home_win_pct": round(home_wins / n_sims, 4),
            "draw_pct": round(draws / n_sims, 4),
            "away_win_pct": round(away_wins / n_sims, 4),
            "home_wins": home_wins,
            "draws": draws,
            "away_wins": away_wins,
            "avg_home_goals": round(avg_home, 2),
            "avg_away_goals": round(avg_away, 2),
            "std_home_goals": round(std_home, 2),
            "std_away_goals": round(std_away, 2),
            "most_common_scores": [
                {
                    "scoreline": f"{home_name} {s[0]}-{s[1]} {away_name}",
                    "count": c,
                    "pct": round(c / n_sims, 4),
                }
                for s, c in most_common
            ],
            "upset_probability": round(upset_pct, 4),
            "favorite": favorite,
            "home_xg": home_xg,
            "away_xg": away_xg,
        }

    def simulate_match_detailed(
        self,
        home_xg: float,
        away_xg: float,
        home_name: str = "Home",
        away_name: str = "Away",
    ) -> Dict[str, Any]:
        """Extended simulation with goal distribution analysis."""
        base = self.simulate_match(home_xg, away_xg, home_name, away_name)

        # Goal distribution
        n_sims = self.n_simulations
        home_goals = self.rng.poisson(lam=max(home_xg, 0.1), size=n_sims)
        away_goals = self.rng.poisson(lam=max(away_xg, 0.1), size=n_sims)
        total_goals = home_goals + away_goals

        base["total_goals_avg"] = round(float(np.mean(total_goals)), 2)
        base["over_1_5_pct"] = round(float(np.mean(total_goals >= 2)), 4)
        base["over_2_5_pct"] = round(float(np.mean(total_goals >= 3)), 4)
        base["over_3_5_pct"] = round(float(np.mean(total_goals >= 4)), 4)
        base["btts_pct"] = round(float(np.mean((home_goals > 0) & (away_goals > 0))), 4)
        base["nil_nil_pct"] = round(float(np.mean((home_goals == 0) & (away_goals == 0))), 4)

        return base
