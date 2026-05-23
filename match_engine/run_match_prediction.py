"""
Run Match Prediction — Generate predictions for key World Cup matchups.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from match_engine.utils.logging_config import setup_logging
from match_engine.probabilities.match_probability import MatchProbabilityEngine

logger = setup_logging("run_match_prediction")

# Key World Cup 2026 matchups to predict
MATCHUPS = [
    ("France", "Brazil"),
    ("Argentina", "Germany"),
    ("Spain", "England"),
    ("Portugal", "Netherlands"),
    ("Italy", "Belgium"),
    ("Japan", "South Korea"),
    ("Mexico", "United States"),
    ("Uruguay", "Colombia"),
    ("Croatia", "Denmark"),
    ("Morocco", "Senegal"),
    ("France", "Argentina"),
    ("Spain", "Germany"),
    ("Brazil", "England"),
    ("Portugal", "France"),
    ("Argentina", "Brazil"),
    ("France", "Bolivia"),
    ("Germany", "Japan"),
    ("Spain", "Morocco"),
    ("United States", "Iran"),
    ("Saudi Arabia", "Mexico"),
]


def main():
    print("\n" + "=" * 70)
    print("⚽  MATCH PREDICTION ENGINE — Batch Run")
    print("=" * 70 + "\n")

    engine = MatchProbabilityEngine()

    results = []
    for home, away in MATCHUPS:
        try:
            result = engine.predict(home, away, venue="neutral", tournament="world_cup_group")
            results.append(result)
            winner = result["predicted_winner"]
            h_prob = result["home_win_prob"]
            d_prob = result["draw_prob"]
            a_prob = result["away_win_prob"]
            xg = f"{result['home_xg']}-{result['away_xg']}"
            print(f"  {home:20s} vs {away:20s} → {winner:20s} | "
                  f"W:{h_prob:.0%} D:{d_prob:.0%} L:{a_prob:.0%} | xG:{xg}")
        except Exception as e:
            logger.warning("Failed: %s vs %s — %s", home, away, e)

    print(f"\n✅ Generated {len(results)} predictions.")
    return results


if __name__ == "__main__":
    main()
