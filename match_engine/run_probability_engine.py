"""
Run Probability Engine — Monte Carlo simulation for key matchups.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from match_engine.utils.logging_config import setup_logging
from match_engine.utils.helpers import normalize_team_name, format_probability
from match_engine.probabilities.match_probability import MatchProbabilityEngine
from match_engine.simulation.monte_carlo import MonteCarloSimulator

logger = setup_logging("probability_engine")

MATCHUPS = [
    ("France", "Brazil"), ("Argentina", "Germany"), ("Spain", "England"),
    ("Portugal", "Netherlands"), ("France", "Bolivia"),
    ("Mexico", "United States"), ("Japan", "South Korea"),
    ("France", "Argentina"), ("Spain", "Germany"), ("Brazil", "England"),
]


def main():
    print("\n" + "=" * 70)
    print("🎰  PROBABILITY ENGINE — Monte Carlo Simulation")
    print("=" * 70 + "\n")

    engine = MatchProbabilityEngine()
    mc = MonteCarloSimulator(n_simulations=10_000)

    for home, away in MATCHUPS:
        try:
            pred = engine.predict(home, away, "neutral", "world_cup_group")
            sim = mc.simulate_match(pred["home_xg"], pred["away_xg"],
                                    pred["home_team"], pred["away_team"])

            print(f"  {pred['home_team']:15s} vs {pred['away_team']:15s}")
            print(f"    Intelligence:  W:{pred['home_win_prob']:.0%} "
                  f"D:{pred['draw_prob']:.0%} L:{pred['away_win_prob']:.0%}")
            print(f"    Monte Carlo:   W:{sim['home_win_pct']:.0%} "
                  f"D:{sim['draw_pct']:.0%} L:{sim['away_win_pct']:.0%}")
            print(f"    Avg Score: {sim['avg_home_goals']:.1f}-{sim['avg_away_goals']:.1f} "
                  f"| Upset: {format_probability(sim['upset_probability'])}")
            print()
        except Exception as e:
            print(f"  ⚠ {home} vs {away}: {e}\n")

    print("✅ Monte Carlo simulation complete.")


if __name__ == "__main__":
    main()
