"""
Monte Carlo Tournament Simulation
=====================================
Runs N complete tournament simulations to generate:
- Champion probabilities
- Stage advancement probabilities
- Group exit probabilities
"""

import logging
import csv
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from collections import defaultdict, Counter

import sys
sys.path.insert(0, str(Path(__file__).parents[2]))

from match_engine.probabilities.match_probability import MatchProbabilityEngine
from ..simulation.tournament import TournamentSimulator
from ..fixtures.generator import load_teams
from ..utils.constants import DEFAULT_MC_SIMULATIONS, MAX_MC_SIMULATIONS, EXPORTS_DIR

logger = logging.getLogger("tournament.monte_carlo")


class MonteCarloTournament:
    """
    Runs multiple tournament simulations and aggregates probabilities.

    Usage:
        mc = MonteCarloTournament(n_simulations=1000, base_seed=2026)
        mc.run()
        mc.export_probabilities()
    """

    def __init__(self, n_simulations: int = DEFAULT_MC_SIMULATIONS,
                 base_seed: int = 2026,
                 prediction_engine: Optional[MatchProbabilityEngine] = None,
                 fixed_results: Optional[Dict[Any, Dict[str, Any]]] = None):
        self._n = min(n_simulations, MAX_MC_SIMULATIONS)
        self._base_seed = base_seed
        self._engine = prediction_engine or MatchProbabilityEngine()
        self._fixed_results = fixed_results or {}

        # Aggregated counts
        self._champion_count: Counter = Counter()
        self._final_count: Counter = Counter()
        self._sf_count: Counter = Counter()
        self._qf_count: Counter = Counter()
        self._r16_count: Counter = Counter()
        self._r32_count: Counter = Counter()
        self._group_advance_count: Counter = Counter()
        self._group_exit_count: Counter = Counter()
        self._expected_goals_for: Counter = Counter()
        self._expected_goals_against: Counter = Counter()
        self._finish_position_total: Counter = Counter()
        self._finish_position_count: Counter = Counter()
        self._upset_count = 0
        self._match_count = 0

        self._completed = 0
        self._all_teams: List[str] = []

    def run(self) -> Dict[str, Any]:
        """Run all simulations."""
        logger.info("=" * 60)
        logger.info("MONTE CARLO TOURNAMENT SIMULATION (%d runs)", self._n)
        logger.info("=" * 60)

        # Load teams once for team list
        teams = load_teams()
        self._all_teams = [t["country_name"] for t in teams]

        for i in range(self._n):
            seed = self._base_seed + i
            sim = TournamentSimulator(
                seed=seed,
                stochastic=True,
                prediction_engine=self._engine,
                fixed_results=self._fixed_results,
            )

            try:
                sim.run()
                self._record_simulation(sim)
                self._completed += 1

                if (i + 1) % max(1, self._n // 10) == 0:
                    logger.info(
                        "  Completed %d/%d simulations (%.0f%%)",
                        i + 1, self._n, (i + 1) / self._n * 100,
                    )
            except Exception as e:
                logger.warning("Simulation %d failed: %s", i, e)

        logger.info("Monte Carlo complete: %d/%d successful", self._completed, self._n)
        return self.get_probabilities()

    def _record_simulation(self, sim: TournamentSimulator):
        """Record results from a single simulation."""
        state = sim.get_tournament_state()

        # Champion
        self._champion_count[state["champion"]] += 1

        # Finalists (both champion and runner-up reached the final)
        self._final_count[state["champion"]] += 1
        self._final_count[state["runner_up"]] += 1

        # Semi-finalists (champion, runner-up, third, fourth)
        for team in [state["champion"], state["runner_up"],
                     state["third_place"], state["fourth_place"]]:
            if team and team != "TBD":
                self._sf_count[team] += 1

        self._record_finish_positions(state)
        self._record_match_stats(state.get("group_results", []), knockout=False)
        self._record_match_stats(state.get("knockout_results", []), knockout=True)

        # Track knockout progression from results
        knockout_results = state.get("knockout_results", [])
        for r in knockout_results:
            stage = r.get("stage", "")
            winner = r.get("winner", "")
            home = r.get("home_team", "")
            away = r.get("away_team", "")

            # Both teams in this stage made it at least to this round
            if stage == "R32":
                self._r32_count[home] += 1
                self._r32_count[away] += 1
            elif stage == "R16":
                self._r16_count[home] += 1
                self._r16_count[away] += 1
            elif stage == "QF":
                self._qf_count[home] += 1
                self._qf_count[away] += 1

        # Group advancement
        advancing = state.get("advancing_teams")
        if advancing:
            for team in advancing.get("all_advancing", []):
                name = team.get("team", "")
                if name:
                    self._group_advance_count[name] += 1

            # Eliminated in group stage
            for team in advancing.get("eliminated_thirds", []):
                self._group_exit_count[team.get("team", "")] += 1
            for team in advancing.get("fourths", []):
                self._group_exit_count[team.get("team", "")] += 1

    def _record_match_stats(self, results: List[Dict[str, Any]], knockout: bool) -> None:
        """Aggregate xG totals and upset frequency."""
        for result in results:
            home = result.get("home_team", "")
            away = result.get("away_team", "")
            home_xg = float(result.get("home_xg", 0.0))
            away_xg = float(result.get("away_xg", 0.0))

            self._expected_goals_for[home] += home_xg
            self._expected_goals_against[home] += away_xg
            self._expected_goals_for[away] += away_xg
            self._expected_goals_against[away] += home_xg
            self._match_count += 1

            if knockout:
                if result.get("is_upset", False):
                    self._upset_count += 1
            else:
                home_prob = float(result.get("home_win_prob", 0.33))
                away_prob = float(result.get("away_win_prob", 0.33))
                favorite = home if home_prob >= away_prob else away
                winner = home if result.get("result") == "home_win" else away if result.get("result") == "away_win" else ""
                if winner and winner != favorite:
                    self._upset_count += 1

    def _record_finish_positions(self, state: Dict[str, Any]) -> None:
        """Assign a finish position to each team in the simulated tournament."""
        assigned: Dict[str, float] = {}

        final_positions = {
            state.get("champion"): 1.0,
            state.get("runner_up"): 2.0,
            state.get("third_place"): 3.0,
            state.get("fourth_place"): 4.0,
        }
        for team, position in final_positions.items():
            if team and team != "TBD":
                assigned[team] = position

        stage_positions = {
            "QF": 6.5,
            "R16": 12.5,
            "R32": 24.5,
        }
        for result in state.get("knockout_results", []):
            loser = result.get("loser", "")
            stage = result.get("stage", "")
            if loser and loser not in assigned and stage in stage_positions:
                assigned[loser] = stage_positions[stage]

        advancing = state.get("advancing_teams") or {}
        advancing_names = {item.get("team", "") for item in advancing.get("all_advancing", [])}
        for team in self._all_teams:
            if team in assigned:
                continue
            if team not in advancing_names:
                assigned[team] = 40.5

        for team, position in assigned.items():
            self._finish_position_total[team] += position
            self._finish_position_count[team] += 1

    def get_probabilities(self) -> Dict[str, Dict[str, float]]:
        """Get advancement probabilities for all teams."""
        n = max(self._completed, 1)
        probs = {}

        for team in self._all_teams:
            probs[team] = {
                "team": team,
                "group_advance_prob": round(self._group_advance_count[team] / n, 4),
                "group_exit_prob": round(self._group_exit_count[team] / n, 4),
                "r32_prob": round(self._r32_count[team] / n, 4),
                "r16_prob": round(self._r16_count[team] / n, 4),
                "qf_prob": round(self._qf_count[team] / n, 4),
                "sf_prob": round(self._sf_count[team] / n, 4),
                "final_prob": round(self._final_count[team] / n, 4),
                "champion_prob": round(self._champion_count[team] / n, 4),
            }

        return probs

    def get_aggregate_statistics(self) -> Dict[str, Any]:
        """Get tournament-level aggregate statistics."""
        n = max(self._completed, 1)
        return {
            "simulations": self._completed,
            "champion_probabilities": {team: round(self._champion_count[team] / n, 4) for team in self._all_teams},
            "semifinal_probabilities": {team: round(self._sf_count[team] / n, 4) for team in self._all_teams},
            "expected_goals": {
                team: {
                    "for": round(self._expected_goals_for[team] / n, 2),
                    "against": round(self._expected_goals_against[team] / n, 2),
                    "difference": round((self._expected_goals_for[team] - self._expected_goals_against[team]) / n, 2),
                }
                for team in self._all_teams
            },
            "upset_frequency": {
                "matches": self._match_count,
                "upsets": self._upset_count,
                "rate": round(self._upset_count / max(self._match_count, 1), 4),
            },
            "average_finish_position": {
                team: round(self._finish_position_total[team] / max(self._finish_position_count[team], 1), 2)
                for team in self._all_teams
            },
        }

    def get_top_champions(self, n: int = 10) -> List[tuple]:
        """Get top N most likely champions."""
        total = max(self._completed, 1)
        return [
            (team, count / total)
            for team, count in self._champion_count.most_common(n)
        ]

    def export_probabilities(self, path: Optional[Path] = None):
        """Export tournament probabilities to CSV."""
        path = path or EXPORTS_DIR / "tournament_probabilities.csv"
        path.parent.mkdir(parents=True, exist_ok=True)

        probs = self.get_probabilities()
        fields = ["team", "group_advance_prob", "group_exit_prob",
                  "r32_prob", "r16_prob", "qf_prob", "sf_prob",
                  "final_prob", "champion_prob"]

        # Sort by champion probability descending
        sorted_teams = sorted(probs.values(),
                             key=lambda x: -x["champion_prob"])

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for team_probs in sorted_teams:
                writer.writerow(team_probs)

        logger.info("Tournament probabilities exported to %s", path)

    def export_summary(self, path: Optional[Path] = None):
        """Export Monte Carlo summary to JSON with comprehensive aggregate statistics."""
        path = path or EXPORTS_DIR / "monte_carlo_summary.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        agg_stats = self.get_aggregate_statistics()

        summary = {
            "simulations": self._completed,
            "top_champions": [
                {"team": t, "probability": round(p, 4)}
                for t, p in self.get_top_champions(20)
            ],
            "all_probabilities": self.get_probabilities(),
            "aggregate_statistics": agg_stats,
            "top_semifinals": [
                {"team": t, "probability": round(self._sf_count[t] / self._completed, 4)}
                for t, _ in sorted(self._sf_count.items(), key=lambda x: -x[1])[:10]
            ] if self._completed > 0 else [],
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        logger.info("Monte Carlo summary exported to %s (with aggregate statistics)", path)

    def export_aggregate_statistics(self, path: Optional[Path] = None):
        """Export comprehensive aggregate tournament statistics to JSON."""
        path = path or EXPORTS_DIR / "tournament_aggregate_stats.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        agg_stats = self.get_aggregate_statistics()

        # Add detailed breakdowns
        detailed_stats = {
            "metadata": {
                "simulations": self._completed,
                "tournament_format": "FIFA World Cup 2026",
                "total_matches": self._match_count,
                "total_upsets": self._upset_count,
            },
            "champion_probabilities": agg_stats.get("champion_probabilities", {}),
            "semifinal_probabilities": agg_stats.get("semifinal_probabilities", {}),
            "expected_goals_stats": agg_stats.get("expected_goals", {}),
            "upset_analysis": agg_stats.get("upset_frequency", {}),
            "average_finish_positions": agg_stats.get("average_finish_position", {}),
            "final_stage_probabilities": {
                team: {
                    "champion": round(self._champion_count[team] / self._completed, 4),
                    "runner_up": round(self._final_count[team] / self._completed, 4) - 
                                  round(self._champion_count[team] / self._completed, 4),
                    "semifinal": round(self._sf_count[team] / self._completed, 4),
                }
                for team in self._all_teams
            } if self._completed > 0 else {},
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(detailed_stats, f, indent=2, ensure_ascii=False)
        logger.info("Aggregate tournament statistics exported to %s", path)
