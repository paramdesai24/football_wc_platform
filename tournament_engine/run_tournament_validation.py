"""
FIFA World Cup 2026 — Tournament Validation
=============================================
Validates tournament integrity and bracket correctness.
"""
import sys
import json
from pathlib import Path

import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from tournament_engine.utils.logging_config import setup_logging
from tournament_engine.utils.constants import EXPORTS_DIR
from tournament_engine.simulation.tournament import TournamentSimulator
from tournament_engine.fixtures.generator import load_teams

logger = setup_logging("tournament.validation", level=logging.WARNING)


def main():
    print("\n" + "=" * 70)
    print("  FIFA WORLD CUP 2026 — TOURNAMENT VALIDATION")
    print("=" * 70)

    teams = load_teams()
    qualified_names = set(t["country_name"] for t in teams)

    # Run a simulation for validation
    sim = TournamentSimulator(seed=2026, stochastic=True)
    sim.run()
    state = sim.get_tournament_state()

    issues = []
    passes = []

    # ── Test 1: All 48 teams present ──
    group_teams = set()
    for group, standings in state["group_standings"].items():
        for s in standings:
            group_teams.add(s["team"])

    if len(group_teams) == 48:
        passes.append("48 teams in group stage")
    else:
        issues.append(f"Expected 48 teams, found {len(group_teams)}")

    # ── Test 2: Only qualified teams ──
    non_qualified = group_teams - qualified_names
    if not non_qualified:
        passes.append("All teams are qualified")
    else:
        issues.append(f"Non-qualified teams found: {non_qualified}")

    # ── Test 3: 12 groups ──
    n_groups = len(state["group_standings"])
    if n_groups == 12:
        passes.append("12 groups present")
    else:
        issues.append(f"Expected 12 groups, found {n_groups}")

    # ── Test 4: 4 teams per group ──
    for group, standings in state["group_standings"].items():
        if len(standings) != 4:
            issues.append(f"Group {group}: {len(standings)} teams (expected 4)")
    if not any("teams (expected 4)" in i for i in issues):
        passes.append("4 teams per group")

    # ── Test 5: 32 advancing teams ──
    advancing = state.get("advancing_teams")
    if advancing:
        n_advancing = len(advancing.get("all_advancing", []))
        if n_advancing == 32:
            passes.append("32 teams advance to knockouts")
        else:
            issues.append(f"Expected 32 advancing, got {n_advancing}")

    # ── Test 6: Knockout bracket integrity ──
    bracket = state.get("bracket", {})
    bracket_issues = sim._bracket.validate()
    if not bracket_issues:
        passes.append("Bracket integrity valid")
    else:
        issues.extend(bracket_issues)

    # ── Test 7: No duplicate teams in R32 ──
    r32_teams = set()
    for m in bracket.get("r32", []):
        for t in [m.get("home_team"), m.get("away_team")]:
            if t and t != "TBD":
                if t in r32_teams:
                    issues.append(f"Duplicate in R32: {t}")
                r32_teams.add(t)
    if not any("Duplicate in R32" in i for i in issues):
        passes.append("No duplicate teams in R32")

    # ── Test 8: Match IDs are correct ──
    ko_ids = [r["match_id"] for r in state["knockout_results"]]
    expected_range = list(range(73, 105))
    missing_ids = set(expected_range) - set(ko_ids)
    if not missing_ids:
        passes.append("All match IDs 73-104 present")
    else:
        issues.append(f"Missing match IDs: {missing_ids}")

    # ── Test 9: Every knockout match has a winner ──
    for r in state["knockout_results"]:
        if not r.get("winner") or r["winner"] == "TBD":
            issues.append(f"M{r['match_id']}: no winner")
    if not any("no winner" in i for i in issues):
        passes.append("All knockout matches have winners")

    # ── Test 10: Champion exists and is qualified ──
    champion = state.get("champion", "")
    if champion and champion in qualified_names:
        passes.append(f"Champion is valid: {champion}")
    else:
        issues.append(f"Invalid champion: {champion}")

    # ── Test 11: Bracket progression is consistent ──
    # Check R16 teams came from R32 winners
    r32_winners = set()
    for m in bracket.get("r32", []):
        w = m.get("winner")
        if w:
            r32_winners.add(w)

    r16_participants = set()
    for m in bracket.get("r16", []):
        for t in [m.get("home_team"), m.get("away_team")]:
            if t and t != "TBD":
                r16_participants.add(t)

    invalid_r16 = r16_participants - r32_winners
    if not invalid_r16:
        passes.append("R16 teams all came from R32 winners")
    else:
        issues.append(f"R16 teams not from R32: {invalid_r16}")

    # ── Test 12: No team plays itself ──
    for r in state["knockout_results"]:
        if r.get("home_team") == r.get("away_team"):
            issues.append(f"M{r['match_id']}: team plays itself")
    if not any("plays itself" in i for i in issues):
        passes.append("No team plays itself")

    # ── Test 13: Elite Stability (Chaos Detection) ──
    elite_teams = {"Brazil", "France", "Argentina", "Spain", "England", 
                   "Germany", "Portugal", "Netherlands", "Belgium", "Italy"}
    r32_matches = [m for m in state.get("knockout_results", []) if m["stage"] == "R32"]
    elite_in_r32 = [m for m in r32_matches if m["home_team"] in elite_teams or m["away_team"] in elite_teams]
    elite_lost_r32 = [m for m in r32_matches if (m["home_team"] in elite_teams or m["away_team"] in elite_teams) and m["winner"] not in elite_teams]
    
    if len(elite_in_r32) > 0 and (len(elite_lost_r32) / len(elite_in_r32)) > 0.6:
        issues.append("Elite teams collapsed in R32 (Excessive Chaos)")
    else:
        passes.append("Elite teams remained stable in R32")

    # ── Test 14: Semifinal Realism ──
    sf_teams = set()
    for m in state.get("knockout_results", []):
        if m["stage"] == "SF":
            sf_teams.add(m["home_team"])
            sf_teams.add(m["away_team"])
    elite_in_sf = [t for t in sf_teams if t in elite_teams]
    if len(elite_in_sf) < 1: # At least 1 elite team should reach SF in 95% of runs
        issues.append(f"Unrealistic Semifinals: 0 elite teams reached SF")
    else:
        passes.append(f"Semifinal distribution realistic ({len(elite_in_sf)} elite teams)")

    # ── Test 15: Champion Realism ──
    high_tier = elite_teams | {"Uruguay", "Croatia", "Morocco", "Switzerland", "USA", "Mexico", "Japan"}
    if champion not in high_tier:
        issues.append(f"Unrealistic Champion: {champion}")
    else:
        passes.append(f"Champion is realistic: {champion}")

    # ── Print results ──
    print()
    for p in passes:
        print(f"  PASS  {p}")

    for i in issues:
        print(f"  FAIL  {i}")

    print(f"\n{'=' * 70}")
    print(f"  RESULTS: {len(passes)} passed, {len(issues)} failed")
    print(f"{'=' * 70}")

    # Save validation report
    report = {
        "passes": passes,
        "issues": issues,
        "total_passes": len(passes),
        "total_issues": len(issues),
        "champion": champion,
    }
    out_path = EXPORTS_DIR / "tournament_validation.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n  Report saved to {out_path}")


if __name__ == "__main__":
    main()
