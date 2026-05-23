"""
Tournament Simulation Orchestrator
======================================
Orchestrates the complete FIFA World Cup 2026 simulation:
Group Stage → Standings → R32 → R16 → QF → SF → 3rd/Final

Produces a complete tournament state that can be saved and resumed.
"""

import json
import logging
import csv
from copy import deepcopy
from typing import Dict, Any, List, Optional
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parents[2]))

from match_engine.probabilities.match_probability import MatchProbabilityEngine
from ..fixtures.generator import load_teams, get_groups, generate_group_fixtures
from ..group_stage.engine import GroupStageEngine
from ..standings.standings_engine import StandingsEngine
from ..knockouts.bracket import BracketEngine
from ..knockouts.knockout_engine import KnockoutMatchEngine
from ..utils.constants import EXPORTS_DIR, GROUP_NAMES
from ..utils.team_state import build_team_state, update_team_state

logger = logging.getLogger("tournament.simulation")


class TournamentSimulator:
    """
    Complete FIFA World Cup 2026 tournament simulation.

    Usage:
        sim = TournamentSimulator(seed=2026)
        sim.run()
        print(sim.champion)
    """

    def __init__(self, seed: Optional[int] = None,
                 stochastic: bool = True,
                 prediction_engine: Optional[MatchProbabilityEngine] = None,
                 fixed_results: Optional[Dict[Any, Dict[str, Any]]] = None):
        self._engine = prediction_engine or MatchProbabilityEngine()
        self._seed = seed
        self._stochastic = stochastic
        self._fixed_results = fixed_results or {}

        # Engines
        self._group_engine = GroupStageEngine(
            prediction_engine=self._engine,
            stochastic=stochastic,
            seed=seed,
        )
        self._standings = StandingsEngine()
        self._bracket = BracketEngine()
        self._knockout_engine = KnockoutMatchEngine(
            prediction_engine=self._engine,
            seed=seed + 1000 if seed else None,
        )

        # State
        self._teams = []
        self._team_state = {}
        self._group_fixtures = []
        self._group_results = []
        self._knockout_results = []
        self._state = "initialized"

    def _get_fixed_result(self, match_id: Any) -> Optional[Dict[str, Any]]:
        return self._fixed_results.get(match_id)

    @staticmethod
    def _team_state_copy(team_state: Optional[Dict[str, Dict[str, Any]]]) -> Optional[Dict[str, Dict[str, Any]]]:
        if team_state is None:
            return None
        return deepcopy(team_state)

    def _apply_fixed_result_team_state(self, result: Dict[str, Any], stage: str) -> None:
        home_team = result.get("home_team")
        away_team = result.get("away_team")
        home_state = self._team_state.get(home_team) if home_team else None
        away_state = self._team_state.get(away_team) if away_team else None

        home_prob = float(result.get("home_win_prob", 0.33))
        away_prob = float(result.get("away_win_prob", 0.33))
        favourite = home_team if home_prob >= away_prob else away_team
        winner = result.get("winner")
        upset = bool(winner and favourite and winner != favourite and abs(home_prob - away_prob) > 0.10)

        update_team_state(
            home_state,
            int(result.get("home_goals", 0)),
            int(result.get("away_goals", 0)),
            stage,
            extra_time=bool(result.get("extra_time", False)),
            penalties=bool(result.get("penalties", False)),
            upset=upset,
        )
        update_team_state(
            away_state,
            int(result.get("away_goals", 0)),
            int(result.get("home_goals", 0)),
            stage,
            extra_time=bool(result.get("extra_time", False)),
            penalties=bool(result.get("penalties", False)),
            upset=upset,
        )

    @property
    def champion(self) -> str:
        return self._bracket.get_champion()

    @property
    def runner_up(self) -> str:
        return self._bracket.get_runner_up()

    @property
    def third_place(self) -> str:
        return self._bracket.get_third_place()

    @property
    def fourth_place(self) -> str:
        return self._bracket.get_fourth_place()

    def run(self) -> Dict[str, Any]:
        """Run the complete tournament simulation."""
        logger.info("=" * 60)
        logger.info("FIFA WORLD CUP 2026 — TOURNAMENT SIMULATION")
        logger.info("=" * 60)

        self.run_group_stage()
        self.run_knockouts()

        logger.info("=" * 60)
        logger.info("CHAMPION: %s", self.champion)
        logger.info("RUNNER-UP: %s", self.runner_up)
        logger.info("THIRD: %s", self.third_place)
        logger.info("FOURTH: %s", self.fourth_place)
        logger.info("=" * 60)

        return self.get_tournament_state()

    def run_group_stage(self) -> Dict[str, List]:
        """Run the complete group stage."""
        logger.info("\n--- GROUP STAGE ---")
        self._teams = load_teams()
        loader_averages = self._engine._loader.league_averages
        self._team_state = {}
        for team in self._teams:
            name = team.get("country_name", "")
            if name:
                base = self._engine._loader.get_team(name)
                if base:
                    self._team_state[name] = build_team_state(base, loader_averages)
        self._group_engine._team_state = self._team_state
        groups = get_groups(self._teams)

        # Initialize standings for all groups
        for group_name, group_teams in groups.items():
            team_names = [t["country_name"] for t in group_teams]
            self._standings.initialize_group(group_name, team_names)

        # Generate and simulate fixtures
        self._group_fixtures = generate_group_fixtures(self._teams)
        self._group_results = []
        grouped_fixtures = sorted(self._group_fixtures, key=lambda fix: (fix["matchday"], fix["match_id"]))
        for fix in grouped_fixtures:
            fixed_result = self._get_fixed_result(fix["match_id"])
            if fixed_result:
                # Consume the same RNG path without mutating the live state, then
                # apply the fixed result so downstream matches see the override.
                self._group_engine.simulate_match(
                    home_team=fix["home_team"],
                    away_team=fix["away_team"],
                    group=fix["group"],
                    matchday=fix["matchday"],
                    match_id=fix["match_id"],
                    team_state=self._team_state_copy(self._team_state),
                )
                result = dict(fixed_result)
                self._apply_fixed_result_team_state(result, "group")
            else:
                result = self._group_engine.simulate_match(
                    home_team=fix["home_team"],
                    away_team=fix["away_team"],
                    group=fix["group"],
                    matchday=fix["matchday"],
                    match_id=fix["match_id"],
                    team_state=self._team_state,
                )
            self._group_results.append(result)
            self._standings.update_from_match(result)

        # Log standings
        for group in sorted(groups.keys()):
            logger.info("\n%s", self._standings.format_standings_table(group))

        self._state = "group_stage_complete"
        return self._standings.get_all_standings()

    def run_knockouts(self):
        """Run the complete knockout stage."""
        logger.info("\n--- KNOCKOUT STAGE ---")

        if self._state != "group_stage_complete":
            self.run_group_stage()

        # Get advancing teams
        advancing = self._standings.get_advancing_teams()
        self._bracket.set_group_results(advancing)

        # R32
        logger.info("\n=== ROUND OF 32 ===")
        r32_fixtures = self._bracket.get_r32_fixtures()
        for fix in r32_fixtures:
            fixed_result = self._get_fixed_result(fix["match_id"])
            if fixed_result:
                self._knockout_engine.simulate(
                    fix["home_team"], fix["away_team"],
                    match_id=fix["match_id"], stage="R32",
                    team_state=self._team_state_copy(self._team_state),
                )
                result = dict(fixed_result)
                self._apply_fixed_result_team_state(result, "R32")
            else:
                result = self._knockout_engine.simulate(
                    fix["home_team"], fix["away_team"],
                    match_id=fix["match_id"], stage="R32",
                    team_state=self._team_state,
                )
            self._bracket.record_result(fix["match_id"], result)
            self._knockout_results.append(result)

        # R16
        logger.info("\n=== ROUND OF 16 ===")
        r16_fixtures = self._bracket.get_r16_fixtures()
        for fix in r16_fixtures:
            fixed_result = self._get_fixed_result(fix["match_id"])
            if fixed_result:
                self._knockout_engine.simulate(
                    fix["home_team"], fix["away_team"],
                    match_id=fix["match_id"], stage="R16",
                    team_state=self._team_state_copy(self._team_state),
                )
                result = dict(fixed_result)
                self._apply_fixed_result_team_state(result, "R16")
            else:
                result = self._knockout_engine.simulate(
                    fix["home_team"], fix["away_team"],
                    match_id=fix["match_id"], stage="R16",
                    team_state=self._team_state,
                )
            self._bracket.record_result(fix["match_id"], result)
            self._knockout_results.append(result)

        # QF
        logger.info("\n=== QUARTER-FINALS ===")
        qf_fixtures = self._bracket.get_qf_fixtures()
        for fix in qf_fixtures:
            fixed_result = self._get_fixed_result(fix["match_id"])
            if fixed_result:
                self._knockout_engine.simulate(
                    fix["home_team"], fix["away_team"],
                    match_id=fix["match_id"], stage="QF",
                    team_state=self._team_state_copy(self._team_state),
                )
                result = dict(fixed_result)
                self._apply_fixed_result_team_state(result, "QF")
            else:
                result = self._knockout_engine.simulate(
                    fix["home_team"], fix["away_team"],
                    match_id=fix["match_id"], stage="QF",
                    team_state=self._team_state,
                )
            self._bracket.record_result(fix["match_id"], result)
            self._knockout_results.append(result)

        # SF
        logger.info("\n=== SEMI-FINALS ===")
        sf_fixtures = self._bracket.get_sf_fixtures()
        for fix in sf_fixtures:
            fixed_result = self._get_fixed_result(fix["match_id"])
            if fixed_result:
                self._knockout_engine.simulate(
                    fix["home_team"], fix["away_team"],
                    match_id=fix["match_id"], stage="SF",
                    team_state=self._team_state_copy(self._team_state),
                )
                result = dict(fixed_result)
                self._apply_fixed_result_team_state(result, "SF")
            else:
                result = self._knockout_engine.simulate(
                    fix["home_team"], fix["away_team"],
                    match_id=fix["match_id"], stage="SF",
                    team_state=self._team_state,
                )
            self._bracket.record_result(fix["match_id"], result)
            self._knockout_results.append(result)

        # Third-place playoff
        logger.info("\n=== THIRD-PLACE PLAYOFF ===")
        third_fix = self._bracket.get_third_place_fixture()
        third_fixed = self._get_fixed_result(103)
        if third_fixed:
            self._knockout_engine.simulate(
                third_fix["home_team"], third_fix["away_team"],
                match_id=103, stage="3rd_place",
                team_state=self._team_state_copy(self._team_state),
            )
            third_result = dict(third_fixed)
            self._apply_fixed_result_team_state(third_result, "3rd_place")
        else:
            third_result = self._knockout_engine.simulate(
                third_fix["home_team"], third_fix["away_team"],
                match_id=103, stage="3rd_place",
                team_state=self._team_state,
            )
        self._bracket.record_result(103, third_result)
        self._knockout_results.append(third_result)

        # Final
        logger.info("\n=== FINAL ===")
        final_fix = self._bracket.get_final_fixture()
        final_fixed = self._get_fixed_result(104)
        if final_fixed:
            self._knockout_engine.simulate(
                final_fix["home_team"], final_fix["away_team"],
                match_id=104, stage="Final",
                team_state=self._team_state_copy(self._team_state),
            )
            final_result = dict(final_fixed)
            self._apply_fixed_result_team_state(final_result, "Final")
        else:
            final_result = self._knockout_engine.simulate(
                final_fix["home_team"], final_fix["away_team"],
                match_id=104, stage="Final",
                team_state=self._team_state,
            )
        self._bracket.record_result(104, final_result)
        self._knockout_results.append(final_result)

        self._state = "complete"

    def get_tournament_state(self) -> Dict[str, Any]:
        """Get complete tournament state for saving/export."""
        return {
            "state": self._state,
            "seed": self._seed,
            "stochastic": self._stochastic,
            "group_standings": self._standings.get_all_standings(),
            "group_results": self._group_results,
            "knockout_results": self._knockout_results,
            "bracket": self._bracket.get_bracket_tree(),
            "champion": self.champion,
            "runner_up": self.runner_up,
            "third_place": self.third_place,
            "fourth_place": self.fourth_place,
            "team_state": deepcopy(self._team_state),
            "advancing_teams": (
                self._standings.get_advancing_teams()
                if self._state != "initialized" else None
            ),
        }

    def save_state(self, path: Optional[Path] = None):
        """Save tournament state to JSON."""
        path = path or EXPORTS_DIR / "tournament_state.json"
        path.parent.mkdir(parents=True, exist_ok=True)

        state = self.get_tournament_state()

        # Make state JSON-serializable
        def _clean(obj):
            if isinstance(obj, dict):
                return {k: _clean(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [_clean(v) for v in obj]
            elif isinstance(obj, (int, float, str, bool, type(None))):
                return obj
            else:
                return str(obj)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(_clean(state), f, indent=2, ensure_ascii=False)
        logger.info("Tournament state saved to %s", path)

    def export_knockout_csv(self, path: Optional[Path] = None):
        """Export knockout results to CSV."""
        path = path or EXPORTS_DIR / "knockout_results.csv"
        path.parent.mkdir(parents=True, exist_ok=True)

        fields = ["match_id", "stage", "home_team", "away_team",
                  "home_goals", "away_goals", "winner", "loser",
                  "extra_time", "penalties", "penalty_score",
                  "home_xg", "away_xg", "result_type"]

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for r in self._knockout_results:
                writer.writerow(r)
        logger.info("Knockout results exported to %s", path)

    def export_group_csv(self, path: Optional[Path] = None):
        """Export group standings to CSV."""
        path = path or EXPORTS_DIR / "group_standings.csv"
        path.parent.mkdir(parents=True, exist_ok=True)

        fields = ["group", "position", "team", "played", "won", "drawn",
                  "lost", "goals_for", "goals_against", "goal_difference", "points"]

        all_standings = self._standings.get_all_standings()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for group, standings in sorted(all_standings.items()):
                for s in standings:
                    writer.writerow(s)
        logger.info("Group standings exported to %s", path)
