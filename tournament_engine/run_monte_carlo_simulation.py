"""
FIFA World Cup 2026 — Monte Carlo Simulation
===============================================
Runs N tournament simulations to generate advancement probabilities.
"""
import sys
from pathlib import Path
import logging

sys.path.insert(0, str(Path(__file__).parent.parent))

from tournament_engine.utils.logging_config import setup_logging
from tournament_engine.simulation.monte_carlo import MonteCarloTournament

# Only show warnings during MC (too much output otherwise)
mc_logger = setup_logging("tournament.monte_carlo", level=logging.WARNING)
mc_logger.setLevel(logging.INFO)


def main():
    n = 100
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except ValueError:
            pass

    print(f"\n{'=' * 70}")
    print(f"  FIFA WORLD CUP 2026 — MONTE CARLO SIMULATION ({n} runs)")
    print(f"{'=' * 70}\n")

    mc = MonteCarloTournament(n_simulations=n, base_seed=2026)
    mc.run()

    # Print champion probabilities
    print(f"\n{'=' * 70}")
    print("  CHAMPION PROBABILITIES")
    print(f"{'=' * 70}")
    for team, prob in mc.get_top_champions(20):
        bar = "#" * int(prob * 100)
        print(f"  {team:<25s} {prob*100:5.1f}%  {bar}")

    # Print full stage probabilities for top 15
    print(f"\n{'=' * 70}")
    print("  STAGE ADVANCEMENT PROBABILITIES (Top 15)")
    print(f"{'=' * 70}")
    probs = mc.get_probabilities()
    sorted_teams = sorted(probs.values(), key=lambda x: -x["champion_prob"])[:15]

    print(f"  {'Team':<20s} {'Group':>6s} {'R32':>6s} {'R16':>6s} "
          f"{'QF':>6s} {'SF':>6s} {'Final':>6s} {'Champ':>6s}")
    print("  " + "-" * 62)
    for t in sorted_teams:
        print(f"  {t['team']:<20s} {t['group_advance_prob']*100:5.1f}% "
              f"{t['r32_prob']*100:5.1f}% {t['r16_prob']*100:5.1f}% "
              f"{t['qf_prob']*100:5.1f}% {t['sf_prob']*100:5.1f}% "
              f"{t['final_prob']*100:5.1f}% {t['champion_prob']*100:5.1f}%")

    # Export
    mc.export_probabilities()
    mc.export_summary()
    mc.export_aggregate_statistics()
    print(f"\n  Exports saved to tournament_engine/exports/")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
