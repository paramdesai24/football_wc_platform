"""
Test Match CLI
===============
Quick command-line interface to predict a single match.

Usage:
    python test_match.py "France" "Brazil"
    python test_match.py "Argentina" "Germany" --venue neutral --tournament world_cup_final
"""

import sys
import os
import argparse

# Ensure match_engine is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from match_engine.utils.logging_config import setup_logging
from match_engine.utils.data_loader import IntelligenceDataLoader
from match_engine.utils.helpers import normalize_team_name, format_probability
from match_engine.probabilities.match_probability import MatchProbabilityEngine
from match_engine.simulation.monte_carlo import MonteCarloSimulator
from match_engine.confidence.confidence_engine import ConfidenceEngine
from match_engine.explainability.explainer import PredictionExplainer

logger = setup_logging("test_match")


def main():
    parser = argparse.ArgumentParser(
        description="FIFA World Cup 2026 — Match Prediction Engine"
    )
    parser.add_argument("home", type=str, help="Home team name")
    parser.add_argument("away", type=str, help="Away team name")
    parser.add_argument("--venue", type=str, default="neutral",
                        choices=["home", "neutral", "away"])
    parser.add_argument("--tournament", type=str, default="world_cup_group",
                        help="Tournament context")
    parser.add_argument("--simulations", type=int, default=10000,
                        help="Monte Carlo simulations")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("⚽  FIFA WORLD CUP 2026 — MATCH PREDICTION ENGINE")
    print("=" * 70)

    # Load intelligence
    loader = IntelligenceDataLoader()
    loader.load_all()

    # Resolve teams
    home_data = loader.get_team(normalize_team_name(args.home))
    away_data = loader.get_team(normalize_team_name(args.away))

    if not home_data:
        print(f"\n❌ Team not found: '{args.home}'")
        print(f"Available teams: {', '.join(loader.list_teams()[:20])}...")
        return
    if not away_data:
        print(f"\n❌ Team not found: '{args.away}'")
        return

    h_name = home_data["country_name"]
    a_name = away_data["country_name"]

    print(f"\n🏟️  {h_name} vs {a_name}")
    print(f"📍 Venue: {args.venue.title()} | 🏆 {args.tournament.replace('_', ' ').title()}")
    print("-" * 70)

    # 1. Match probability prediction
    engine = MatchProbabilityEngine(loader)
    prediction = engine.predict(args.home, args.away, args.venue, args.tournament)

    # 2. Confidence scoring
    conf_engine = ConfidenceEngine()
    confidence = conf_engine.score(home_data, away_data)

    # 3. Monte Carlo simulation
    mc = MonteCarloSimulator(n_simulations=args.simulations)
    sim = mc.simulate_match(
        prediction["home_xg"], prediction["away_xg"], h_name, a_name
    )

    # 4. Explainability
    explainer = PredictionExplainer()
    explanation = explainer.explain(prediction, home_data, away_data, confidence)

    # ── Display Results ──────────────────────────────────────

    print(f"\n📊 WINNER PREDICTION")
    print(f"   🏆 Predicted Winner: {prediction['predicted_winner']}")
    print(f"   {h_name} Win:  {format_probability(prediction['home_win_prob'])}")
    print(f"   Draw:         {format_probability(prediction['draw_prob'])}")
    print(f"   {a_name} Win:  {format_probability(prediction['away_win_prob'])}")

    print(f"\n⚽ EXPECTED GOALS")
    print(f"   {h_name}: {prediction['home_xg']} xG")
    print(f"   {a_name}: {prediction['away_xg']} xG")
    print(f"   Total: {prediction['total_xg']} xG")

    print(f"\n📋 PREDICTED SCORELINE")
    print(f"   🎯 {prediction['predicted_score']} (prob: {format_probability(prediction['score_probability'])})")
    print(f"\n   Top Scorelines:")
    for i, s in enumerate(prediction["top_scorelines"][:5], 1):
        print(f"   {i}. {s['scoreline']} — {format_probability(s['probability'])}")

    print(f"\n🎰 MONTE CARLO SIMULATION ({sim['simulations']:,} simulations)")
    print(f"   {h_name} Wins: {format_probability(sim['home_win_pct'])}")
    print(f"   Draws:         {format_probability(sim['draw_pct'])}")
    print(f"   {a_name} Wins: {format_probability(sim['away_win_pct'])}")
    print(f"   Avg Score: {sim['avg_home_goals']:.1f} - {sim['avg_away_goals']:.1f}")
    if sim.get("upset_probability", 0) > 0:
        print(f"   Upset Prob: {format_probability(sim['upset_probability'])}")

    print(f"\n🔒 CONFIDENCE")
    print(f"   Score: {format_probability(confidence['confidence_score'])} ({confidence['confidence_tier']})")

    print(f"\n💡 EXPLANATION")
    print(f"   {explanation['narrative']}")
    if explanation.get("key_factors"):
        print(f"\n   Key Factors:")
        for f in explanation["key_factors"]:
            print(f"   • {f}")

    print(f"\n📈 MARKETS")
    markets = prediction.get("markets", {})
    print(f"   Over 2.5 goals: {format_probability(markets.get('over_2_5', 0))}")
    print(f"   BTTS: {format_probability(markets.get('btts', 0))}")

    print("\n" + "=" * 70)
    print("✅ Prediction complete.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
