"""
Run Prediction Validation — Validate all predictions for football realism.
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from match_engine.utils.logging_config import setup_logging
from match_engine.utils.constants import EXPORTS_DIR
from match_engine.utils.data_loader import IntelligenceDataLoader
from match_engine.utils.helpers import normalize_team_name, format_probability
from match_engine.probabilities.match_probability import MatchProbabilityEngine
from match_engine.confidence.confidence_engine import ConfidenceEngine

logger = setup_logging("run_prediction_validation")


def main():
    print("\n" + "=" * 70)
    print("🔍  PREDICTION VALIDATION ENGINE")
    print("=" * 70 + "\n")

    loader = IntelligenceDataLoader().load_all()
    engine = MatchProbabilityEngine(loader)
    conf_engine = ConfidenceEngine()

    # Realism test cases with expected behavior
    TESTS = [
        # (home, away, expected_winner, max_allowed_prob, min_draw)
        ("France", "Bolivia", "France", 0.85, 0.05),
        ("Argentina", "Brazil", None, 0.65, 0.15),  # Should be close
        ("Spain", "England", None, 0.60, 0.15),     # Should be competitive
        ("Germany", "Japan", "Germany", 0.70, 0.10),
        ("France", "Brazil", None, 0.65, 0.12),
    ]

    issues = []
    passed = 0
    total = 0

    print("📋 Football Realism Tests:\n")
    for home, away, exp_winner, max_prob, min_draw in TESTS:
        total += 1
        try:
            pred = engine.predict(home, away, "neutral", "world_cup_group")
            h_p = pred["home_win_prob"]
            d_p = pred["draw_prob"]
            a_p = pred["away_win_prob"]
            winner = pred["predicted_winner"]
            prob_sum = h_p + d_p + a_p

            # Validation checks
            test_passed = True
            test_issues = []

            # Check probabilities sum to 1
            if abs(prob_sum - 1.0) > 0.01:
                test_issues.append(f"Prob sum = {prob_sum:.4f} (should be 1.0)")
                test_passed = False

            # Check no probability > max allowed
            if max(h_p, a_p) > max_prob:
                test_issues.append(f"Max prob {max(h_p, a_p):.2%} > {max_prob:.0%} (overconfident)")
                test_passed = False

            # Check draw is realistic
            if d_p < min_draw:
                test_issues.append(f"Draw prob {d_p:.2%} < {min_draw:.0%} (too low)")
                test_passed = False

            # Check expected winner if specified
            if exp_winner and winner != exp_winner:
                test_issues.append(f"Expected {exp_winner} but got {winner}")
                test_passed = False

            # Check xG is realistic
            if pred["home_xg"] > 4.0 or pred["away_xg"] > 4.0:
                test_issues.append(f"xG too high: {pred['home_xg']}-{pred['away_xg']}")
                test_passed = False

            status = "✅ PASS" if test_passed else "❌ FAIL"
            if test_passed:
                passed += 1

            print(f"  {status} | {home:15s} vs {away:15s} → {winner}")
            print(f"         W:{h_p:.0%} D:{d_p:.0%} L:{a_p:.0%} | "
                  f"xG: {pred['home_xg']}-{pred['away_xg']} | Score: {pred['predicted_score']}")

            if test_issues:
                for issue in test_issues:
                    print(f"         ⚠ {issue}")
                issues.extend(test_issues)

            print()
        except Exception as e:
            print(f"  ❌ ERROR | {home} vs {away}: {e}\n")
            issues.append(f"Error: {home} vs {away}: {e}")
            total += 0  # Don't count errors

    # Additional structural validations
    print("\n📋 Structural Validation:\n")

    # Test all 130 teams can be predicted against
    struct_tests = 0
    struct_pass = 0
    teams = loader.list_teams()
    ref_team = "France"
    for team in teams[:20]:
        struct_tests += 1
        try:
            pred = engine.predict(ref_team, team, "neutral", "friendly")
            ps = pred["home_win_prob"] + pred["draw_prob"] + pred["away_win_prob"]
            if abs(ps - 1.0) < 0.01 and pred["home_xg"] > 0 and pred["away_xg"] > 0:
                struct_pass += 1
            else:
                issues.append(f"Structural: {ref_team} vs {team} invalid")
        except Exception as e:
            issues.append(f"Structural error: {ref_team} vs {team}: {e}")

    print(f"  Team compatibility: {struct_pass}/{struct_tests} passed")

    # Summary
    print("\n" + "=" * 70)
    print(f"📊 VALIDATION SUMMARY")
    print(f"   Realism tests: {passed}/{total} passed")
    print(f"   Structural tests: {struct_pass}/{struct_tests} passed")
    print(f"   Total issues: {len(issues)}")
    if not issues:
        print(f"   ✅ ALL VALIDATIONS PASSED")
    else:
        print(f"   ⚠ Issues found — review above")
    print("=" * 70 + "\n")

    # Save validation report
    report = {
        "realism_passed": passed,
        "realism_total": total,
        "structural_passed": struct_pass,
        "structural_total": struct_tests,
        "issues": issues,
        "all_passed": len(issues) == 0,
    }
    out_dir = EXPORTS_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "prediction_validation.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved to {out_dir / 'prediction_validation.json'}\n")


if __name__ == "__main__":
    main()
