"""
FIFA World Cup 2026 — Full Tournament Simulation
===================================================
Runs a complete single-pass tournament simulation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tournament_engine.utils.logging_config import setup_logging
from tournament_engine.simulation.tournament import TournamentSimulator

logger = setup_logging("tournament")


def main():
    seed = 2026
    if len(sys.argv) > 1:
        try:
            seed = int(sys.argv[1])
        except ValueError:
            pass

    print("\n" + "=" * 70)
    print("  FIFA WORLD CUP 2026 — TOURNAMENT SIMULATION")
    print("=" * 70)

    sim = TournamentSimulator(seed=seed, stochastic=True)
    sim.run()

    # Print final standings for all groups
    standings = sim._standings.get_all_standings()
    print("\n" + "=" * 70)
    print("  GROUP STAGE FINAL STANDINGS")
    print("=" * 70)
    for group in sorted(standings.keys()):
        print()
        print(sim._standings.format_standings_table(group))

    # Print knockout bracket summary
    print("\n" + "=" * 70)
    print("  KNOCKOUT BRACKET")
    print("=" * 70)
    for r in sim._knockout_results:
        et_marker = ""
        if r.get("penalties"):
            et_marker = f" [PEN {r['penalty_score']}]"
        elif r.get("extra_time"):
            et_marker = " [AET]"

        print(f"  M{r['match_id']:>3d} [{r['stage']:>9s}]  "
              f"{r['home_team']:>20s} {r['home_goals']}-{r['away_goals']} "
              f"{r['away_team']:<20s}{et_marker}")

    # Print final results
    print("\n" + "=" * 70)
    print(f"  CHAMPION:   {sim.champion}")
    print(f"  RUNNER-UP:  {sim.runner_up}")
    print(f"  THIRD:      {sim.third_place}")
    print(f"  FOURTH:     {sim.fourth_place}")
    print("=" * 70)

    # Save state and exports
    sim.save_state()
    sim.export_knockout_csv()
    sim.export_group_csv()
    print("\n  Exports saved to tournament_engine/exports/")


if __name__ == "__main__":
    main()
