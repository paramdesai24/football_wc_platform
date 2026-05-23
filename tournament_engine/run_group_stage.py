"""
FIFA World Cup 2026 — Group Stage Runner
==========================================
Generates fixtures and simulates group stage only.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tournament_engine.utils.logging_config import setup_logging
from tournament_engine.fixtures.generator import load_teams, generate_group_fixtures, save_fixtures, save_groups, get_groups
from tournament_engine.group_stage.engine import GroupStageEngine
from tournament_engine.standings.standings_engine import StandingsEngine

logger = setup_logging("group_stage")


def main():
    print("\n" + "=" * 70)
    print("  FIFA WORLD CUP 2026 — GROUP STAGE SIMULATION")
    print("=" * 70)

    # Generate fixtures
    teams = load_teams()
    save_groups(teams)
    fixtures = generate_group_fixtures(teams)
    save_fixtures(fixtures)

    # Initialize
    groups = get_groups(teams)
    standings = StandingsEngine()
    for group_name, group_teams in groups.items():
        standings.initialize_group(group_name, [t["country_name"] for t in group_teams])

    # Simulate
    engine = GroupStageEngine(stochastic=True, seed=2026)
    results = engine.simulate_all_group_matches(fixtures)
    standings.update_from_results(results)

    # Print standings
    print("\n" + "=" * 70)
    print("  FINAL GROUP STANDINGS")
    print("=" * 70)
    for group in sorted(groups.keys()):
        print()
        print(standings.format_standings_table(group))

    # Print advancing teams
    advancing = standings.get_advancing_teams()
    print("\n" + "=" * 70)
    print("  ADVANCING TO KNOCKOUT STAGE")
    print("=" * 70)
    print("\n  Group Winners:")
    for t in advancing["group_winners"]:
        print(f"    {t['group']}: {t['team']} ({t['points']}pts, GD:{t['goal_difference']:+d})")
    print("\n  Group Runners-Up:")
    for t in advancing["group_runners"]:
        print(f"    {t['group']}: {t['team']} ({t['points']}pts, GD:{t['goal_difference']:+d})")
    print("\n  Best Third-Place Teams:")
    for t in advancing["best_thirds"]:
        grp = t.get("source_group", t.get("group", "?"))
        print(f"    {grp}: {t['team']} ({t['points']}pts, GD:{t['goal_difference']:+d})")

    print(f"\n  Total advancing: {len(advancing['all_advancing'])} teams")
    print("=" * 70)


if __name__ == "__main__":
    main()
