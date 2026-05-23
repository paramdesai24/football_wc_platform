"""
Run Prediction Exports — Export all predictions to CSV and SQLite.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from match_engine.utils.logging_config import setup_logging
from match_engine.utils.data_loader import IntelligenceDataLoader
from match_engine.utils.helpers import normalize_team_name
from match_engine.probabilities.match_probability import MatchProbabilityEngine
from match_engine.confidence.confidence_engine import ConfidenceEngine
from match_engine.explainability.explainer import PredictionExplainer
from match_engine.exports.exporter import PredictionExporter

logger = setup_logging("run_prediction_exports")

# Generate predictions for all interesting WC matchups
MATCHUPS = [
    ("France", "Brazil"), ("Argentina", "Germany"), ("Spain", "England"),
    ("Portugal", "Netherlands"), ("Italy", "Belgium"), ("Japan", "South Korea"),
    ("Mexico", "United States"), ("Uruguay", "Colombia"), ("Croatia", "Denmark"),
    ("Morocco", "Senegal"), ("France", "Argentina"), ("Spain", "Germany"),
    ("Brazil", "England"), ("Portugal", "France"), ("Argentina", "Brazil"),
    ("France", "Bolivia"), ("Germany", "Japan"), ("Spain", "Morocco"),
    ("United States", "Iran"), ("Saudi Arabia", "Mexico"),
    ("Australia", "Tunisia"), ("Canada", "Costa Rica"), ("Serbia", "Switzerland"),
    ("Poland", "Senegal"), ("Ecuador", "Paraguay"), ("Nigeria", "Ghana"),
    ("Cameroon", "Algeria"), ("South Korea", "Australia"),
    ("Chile", "Peru"), ("Wales", "Scotland"),
]


def main():
    print("\n" + "=" * 70)
    print("📦  PREDICTION EXPORT ENGINE")
    print("=" * 70 + "\n")

    loader = IntelligenceDataLoader().load_all()
    engine = MatchProbabilityEngine(loader)
    conf_engine = ConfidenceEngine()
    explainer = PredictionExplainer()
    exporter = PredictionExporter()

    predictions = []
    explanations = []

    for home_name, away_name in MATCHUPS:
        try:
            pred = engine.predict(home_name, away_name, "neutral", "world_cup_group")

            # Confidence
            home_data = loader.get_team(normalize_team_name(home_name))
            away_data = loader.get_team(normalize_team_name(away_name))
            if home_data and away_data:
                conf = conf_engine.score(home_data, away_data)
                pred["confidence_score"] = conf["confidence_score"]
                pred["confidence_tier"] = conf["confidence_tier"]

                # Explainability
                expl = explainer.explain(pred, home_data, away_data, conf)
                pred["explanation"] = expl["narrative"]
                explanations.append(expl)

            predictions.append(pred)
            print(f"  ✓ {home_name} vs {away_name}")
        except Exception as e:
            print(f"  ✗ {home_name} vs {away_name}: {e}")

    print(f"\n📊 Generated {len(predictions)} predictions. Exporting...\n")

    # Export everything
    exporter.export_predictions_csv(predictions)
    exporter.export_expected_goals_csv(predictions)
    exporter.export_scoreline_probs_csv(predictions)
    exporter.export_explainability_csv(explanations)
    exporter.export_to_sqlite(predictions)
    exporter.export_validation_json(predictions)

    print(f"\n✅ All exports complete.")


if __name__ == "__main__":
    main()
