"""
Run Score Prediction — Generate expected goals and scoreline predictions.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from match_engine.utils.logging_config import setup_logging
from match_engine.utils.data_loader import IntelligenceDataLoader
from match_engine.utils.helpers import normalize_team_name, format_probability
from match_engine.score_prediction.expected_goals import ExpectedGoalsEngine
from match_engine.score_prediction.poisson_model import PoissonScoreModel

logger = setup_logging("run_score_prediction")

MATCHUPS = [
    ("France", "Brazil"), ("Argentina", "Germany"), ("Spain", "England"),
    ("Portugal", "Netherlands"), ("Morocco", "Senegal"),
    ("Japan", "South Korea"), ("Mexico", "United States"),
    ("France", "Bolivia"), ("Uruguay", "Colombia"), ("Croatia", "Denmark"),
]


def main():
    print("\n" + "=" * 70)
    print("⚽  SCORE PREDICTION ENGINE")
    print("=" * 70 + "\n")

    loader = IntelligenceDataLoader().load_all()
    xg_engine = ExpectedGoalsEngine(loader.league_averages)
    poisson = PoissonScoreModel()

    results = []
    for home_name, away_name in MATCHUPS:
        home = loader.get_team(normalize_team_name(home_name))
        away = loader.get_team(normalize_team_name(away_name))
        if not home or not away:
            print(f"  ⚠ Skipping {home_name} vs {away_name} — team not found")
            continue

        xg = xg_engine.compute(home, away, "neutral", "world_cup_group")
        score = poisson.predict(xg["home_xg"], xg["away_xg"],
                                home["country_name"], away["country_name"])

        results.append({**xg, **score, "home_team": home["country_name"],
                        "away_team": away["country_name"]})

        print(f"  {home['country_name']:15s} {xg['home_xg']:.2f} xG  |  "
              f"{xg['away_xg']:.2f} xG  {away['country_name']:15s}")
        print(f"  {'':15s} Predicted: {score['predicted_score']}")
        print(f"  {'':15s} Top: ", end="")
        for s in score["top_scorelines"][:3]:
            print(f"{s['home_goals']}-{s['away_goals']}({format_probability(s['probability'])})", end="  ")
        print("\n")

    print(f"✅ Generated {len(results)} score predictions.")
    return results


if __name__ == "__main__":
    main()
