"""
FIFA World Cup 2026 — Knockout Stage Runner
=============================================
Runs group stage + knockout bracket simulation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tournament_engine.utils.logging_config import setup_logging
from tournament_engine.simulation.tournament import TournamentSimulator

logger = setup_logging("knockouts")


def main():
    seed = 2026
    if len(sys.argv) > 1:
        try:
            seed = int(sys.argv[1])
        except ValueError:
            pass

    print("\n" + "=" * 70)
    print("  FIFA WORLD CUP 2026 — KNOCKOUT STAGE")
    print("=" * 70)

    sim = TournamentSimulator(seed=seed, stochastic=True)
    sim.run()

    # Print knockout bracket
    print("\n" + "=" * 70)
    print("  KNOCKOUT BRACKET")
    print("=" * 70)

    stages = {"R32": "Round of 32", "R16": "Round of 16",
              "QF": "Quarter-Finals", "SF": "Semi-Finals",
              "3rd_place": "Third Place", "Final": "FINAL"}
    current_stage = ""
    for r in sim._knockout_results:
        if r["stage"] != current_stage:
            current_stage = r["stage"]
            print(f"\n  --- {stages.get(current_stage, current_stage)} ---")

        et_marker = ""
        if r.get("penalties"):
            et_marker = f" [PEN {r['penalty_score']}]"
        elif r.get("extra_time"):
            et_marker = " [AET]"

        print(f"    M{r['match_id']:>3d}  {r['home_team']:>22s} {r['home_goals']}-{r['away_goals']} "
              f"{r['away_team']:<22s}{et_marker}  → {r['winner']}")

    print(f"\n{'=' * 70}")
    print(f"  🏆 CHAMPION:   {sim.champion}")
    print(f"  🥈 RUNNER-UP:  {sim.runner_up}")
    print(f"  🥉 THIRD:      {sim.third_place}")
    print(f"     FOURTH:     {sim.fourth_place}")
    print(f"{'=' * 70}")

    sim.export_knockout_csv()
    sim.export_group_csv()
    sim.save_state()


if __name__ == "__main__":
    main()
