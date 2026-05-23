"""
FIFA World Cup 2026 — Official Knockout Bracket Engine
=========================================================
Implements the EXACT FIFA predefined bracket structure.

Match IDs 73-102 are FIXED. Only the teams that fill each
slot change based on group-stage results.

Bracket paths:
  R32 (73-88) → R16 (89-96) → QF (97-100) → SF (101-102) → Final

Third-place team assignment follows FIFA's predetermined mapping
based on which 8 of 12 groups produce advancing 3rd-place teams.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import OrderedDict

logger = logging.getLogger("tournament.bracket")


# ─────────────────────────────────────────────────────────────
# FIXED FIFA BRACKET STRUCTURE
# ─────────────────────────────────────────────────────────────
# Each R32 match specifies its two slots.
# "1A" = Winner of Group A, "2B" = Runner-up of Group B
# "3rd(X/Y/Z)" = Third-place team from one of the listed groups

R32_MATCHES = OrderedDict({
    73: {"home_slot": "2A",  "away_slot": "2B",  "third_pool": None},
    74: {"home_slot": "1C",  "away_slot": "2F",  "third_pool": None},
    75: {"home_slot": "1E",  "away_slot": "3rd", "third_pool": ["A", "B", "C", "D", "F"]},
    76: {"home_slot": "1F",  "away_slot": "2C",  "third_pool": None},
    77: {"home_slot": "2E",  "away_slot": "2I",  "third_pool": None},
    78: {"home_slot": "1I",  "away_slot": "3rd", "third_pool": ["C", "D", "F", "G", "H"]},
    79: {"home_slot": "1A",  "away_slot": "3rd", "third_pool": ["C", "E", "F", "H", "I"]},
    80: {"home_slot": "1L",  "away_slot": "3rd", "third_pool": ["E", "H", "I", "J", "K"]},
    81: {"home_slot": "1G",  "away_slot": "3rd", "third_pool": ["A", "E", "H", "I", "J"]},
    82: {"home_slot": "1D",  "away_slot": "3rd", "third_pool": ["B", "E", "F", "I", "J"]},
    83: {"home_slot": "1H",  "away_slot": "2J",  "third_pool": None},
    84: {"home_slot": "2K",  "away_slot": "2L",  "third_pool": None},
    85: {"home_slot": "1B",  "away_slot": "3rd", "third_pool": ["E", "F", "G", "I", "J"]},
    86: {"home_slot": "2D",  "away_slot": "2G",  "third_pool": None},
    87: {"home_slot": "1J",  "away_slot": "2H",  "third_pool": None},
    88: {"home_slot": "1K",  "away_slot": "3rd", "third_pool": ["D", "E", "I", "J", "L"]},
})

# ─── ROUND OF 16: Fixed progression from R32 ─────────────
R16_MATCHES = OrderedDict({
    89: {"home_from": 73, "away_from": 75},
    90: {"home_from": 74, "away_from": 77},
    91: {"home_from": 76, "away_from": 78},
    92: {"home_from": 79, "away_from": 80},
    93: {"home_from": 83, "away_from": 84},
    94: {"home_from": 81, "away_from": 82},
    95: {"home_from": 85, "away_from": 87},
    96: {"home_from": 86, "away_from": 88},
})

# ─── QUARTER-FINALS: Fixed progression from R16 ──────────
QF_MATCHES = OrderedDict({
    97:  {"home_from": 89, "away_from": 90},
    98:  {"home_from": 93, "away_from": 94},
    99:  {"home_from": 91, "away_from": 92},
    100: {"home_from": 95, "away_from": 96},
})

# ─── SEMI-FINALS: Fixed progression from QF ──────────────
SF_MATCHES = OrderedDict({
    101: {"home_from": 97, "away_from": 98},
    102: {"home_from": 99, "away_from": 100},
})

# ─── THIRD-PLACE PLAYOFF & FINAL ─────────────────────────
THIRD_PLACE_MATCH = {"match_id": 103, "home_from": "L101", "away_from": "L102"}
FINAL_MATCH = {"match_id": 104, "home_from": "W101", "away_from": "W102"}


class BracketEngine:
    """
    Deterministic FIFA bracket engine.

    The bracket structure is FIXED — only the teams that fill
    each slot change based on group-stage results.
    """

    def __init__(self):
        # match_id → result dict (includes winner, loser, score)
        self._results: Dict[int, Dict[str, Any]] = {}
        # Group standings data
        self._group_winners: Dict[str, str] = {}   # group → team name
        self._group_runners: Dict[str, str] = {}   # group → team name
        self._best_thirds: List[Dict] = []          # sorted list of advancing 3rds
        self._third_assignments: Dict[int, str] = {} # match_id → assigned 3rd team

    def set_group_results(self, advancing: Dict[str, Any]):
        """
        Set group-stage results for bracket resolution.

        Args:
            advancing: Dict from StandingsEngine.get_advancing_teams()
                       with keys: group_winners, group_runners, best_thirds
        """
        # Map group winners and runners-up
        for team in advancing["group_winners"]:
            self._group_winners[team["group"]] = team["team"]
        for team in advancing["group_runners"]:
            self._group_runners[team["group"]] = team["team"]

        self._best_thirds = advancing["best_thirds"]

        # Resolve third-place assignments
        self._resolve_third_place_assignments()

        logger.info("Bracket initialized: %d winners, %d runners, %d thirds",
                     len(self._group_winners), len(self._group_runners),
                     len(self._best_thirds))

    def _resolve_third_place_assignments(self):
        """
        Assign third-place teams to bracket slots using backtracking
        constraint satisfaction.

        Each R32 match with a third-place slot has a POOL of eligible
        source groups. We must assign exactly one qualifying 3rd-place
        team to each slot such that:
        - Each slot gets a team from its eligible pool
        - No team is assigned to more than one slot
        - All 8 slots are filled

        Uses recursive backtracking to guarantee a valid assignment.
        """
        self._third_assignments = {}
        qualifying_groups = set()
        third_by_group = {}

        for t in self._best_thirds:
            grp = t.get("source_group", t.get("group", ""))
            qualifying_groups.add(grp)
            third_by_group[grp] = t["team"]

        # Collect all slots that need a third-place team
        third_slots = sorted([
            (mid, info["third_pool"])
            for mid, info in R32_MATCHES.items()
            if info["third_pool"] is not None
        ])

        # Build ranked preference for each slot (best 3rd first)
        third_ranking = []
        for t in self._best_thirds:
            grp = t.get("source_group", t.get("group", ""))
            third_ranking.append(grp)

        # Backtracking solver
        assignment = {}  # mid → group

        def _solve(slot_idx: int, used: set) -> bool:
            if slot_idx == len(third_slots):
                return True  # All slots assigned

            mid, pool = third_slots[slot_idx]
            # Try each qualifying group in ranked order (best 3rd first)
            for grp in third_ranking:
                if grp in pool and grp in qualifying_groups and grp not in used:
                    assignment[mid] = grp
                    used.add(grp)
                    if _solve(slot_idx + 1, used):
                        return True
                    # Backtrack
                    del assignment[mid]
                    used.discard(grp)

            return False

        if _solve(0, set()):
            for mid, grp in assignment.items():
                self._third_assignments[mid] = third_by_group[grp]
                logger.info("  M%d: 3rd-place from Group %s → %s",
                           mid, grp, third_by_group[grp])
        else:
            # Fallback: greedy assignment if backtracking fails
            logger.warning("Backtracking failed — using greedy fallback")
            assigned = set()
            for mid, pool in third_slots:
                available = [g for g in pool
                             if g in qualifying_groups and g not in assigned]
                if available:
                    choice = available[0]
                    self._third_assignments[mid] = third_by_group[choice]
                    assigned.add(choice)
                else:
                    # Last resort: assign any remaining team
                    remaining = qualifying_groups - assigned
                    if remaining:
                        choice = next(iter(remaining))
                        self._third_assignments[mid] = third_by_group[choice]
                        assigned.add(choice)
                        logger.warning("  M%d: forced assignment from Group %s", mid, choice)

    def resolve_slot(self, slot: str, match_id: int = 0) -> str:
        """
        Resolve a bracket slot to a team name.

        Args:
            slot: e.g. "1A", "2B", "3rd"
            match_id: for third-place resolution
        """
        if slot == "3rd":
            return self._third_assignments.get(match_id, "TBD")
        elif slot.startswith("1"):
            group = slot[1]
            return self._group_winners.get(group, "TBD")
        elif slot.startswith("2"):
            group = slot[1]
            return self._group_runners.get(group, "TBD")
        return "TBD"

    def get_r32_fixtures(self) -> List[Dict[str, Any]]:
        """Generate Round of 32 fixtures with resolved teams."""
        fixtures = []
        for match_id, info in R32_MATCHES.items():
            home = self.resolve_slot(info["home_slot"], match_id)
            away = self.resolve_slot(info["away_slot"], match_id)
            fixtures.append({
                "match_id": match_id,
                "stage": "R32",
                "home_team": home,
                "away_team": away,
                "home_slot": info["home_slot"],
                "away_slot": info["away_slot"] if info["third_pool"] is None
                             else f"3rd({'/'.join(info['third_pool'])})",
            })
        return fixtures

    def get_r16_fixtures(self) -> List[Dict[str, Any]]:
        """Generate R16 fixtures (requires R32 results)."""
        fixtures = []
        for match_id, info in R16_MATCHES.items():
            home = self._get_winner(info["home_from"])
            away = self._get_winner(info["away_from"])
            fixtures.append({
                "match_id": match_id,
                "stage": "R16",
                "home_team": home,
                "away_team": away,
                "home_from": f"W{info['home_from']}",
                "away_from": f"W{info['away_from']}",
            })
        return fixtures

    def get_qf_fixtures(self) -> List[Dict[str, Any]]:
        """Generate QF fixtures (requires R16 results)."""
        fixtures = []
        for match_id, info in QF_MATCHES.items():
            home = self._get_winner(info["home_from"])
            away = self._get_winner(info["away_from"])
            fixtures.append({
                "match_id": match_id,
                "stage": "QF",
                "home_team": home,
                "away_team": away,
                "home_from": f"W{info['home_from']}",
                "away_from": f"W{info['away_from']}",
            })
        return fixtures

    def get_sf_fixtures(self) -> List[Dict[str, Any]]:
        """Generate SF fixtures (requires QF results)."""
        fixtures = []
        for match_id, info in SF_MATCHES.items():
            home = self._get_winner(info["home_from"])
            away = self._get_winner(info["away_from"])
            fixtures.append({
                "match_id": match_id,
                "stage": "SF",
                "home_team": home,
                "away_team": away,
                "home_from": f"W{info['home_from']}",
                "away_from": f"W{info['away_from']}",
            })
        return fixtures

    def get_third_place_fixture(self) -> Dict[str, Any]:
        """Generate third-place playoff fixture (requires SF results)."""
        return {
            "match_id": 103,
            "stage": "3rd_place",
            "home_team": self._get_loser(101),
            "away_team": self._get_loser(102),
            "home_from": "L101",
            "away_from": "L102",
        }

    def get_final_fixture(self) -> Dict[str, Any]:
        """Generate Final fixture (requires SF results)."""
        return {
            "match_id": 104,
            "stage": "Final",
            "home_team": self._get_winner(101),
            "away_team": self._get_winner(102),
            "home_from": "W101",
            "away_from": "W102",
        }

    def record_result(self, match_id: int, result: Dict[str, Any]):
        """Record a knockout match result."""
        self._results[match_id] = result
        logger.info("  M%d: %s %d-%d %s (%s)%s",
                    match_id,
                    result["home_team"], result["home_goals"],
                    result["away_goals"], result["away_team"],
                    result["stage"],
                    f" [ET]" if result.get("extra_time") else
                    f" [PEN {result.get('penalty_score','')}]" if result.get("penalties") else "")

    def _get_winner(self, match_id: int) -> str:
        """Get the winner of a completed match."""
        result = self._results.get(match_id)
        if result is None:
            return "TBD"
        return result.get("winner", "TBD")

    def _get_loser(self, match_id: int) -> str:
        """Get the loser of a completed match."""
        result = self._results.get(match_id)
        if result is None:
            return "TBD"
        return result.get("loser", "TBD")

    def get_champion(self) -> str:
        """Get the tournament champion."""
        return self._get_winner(104)

    def get_runner_up(self) -> str:
        """Get the tournament runner-up."""
        return self._get_loser(104)

    def get_third_place(self) -> str:
        """Get the third-place team."""
        return self._get_winner(103)

    def get_fourth_place(self) -> str:
        """Get the fourth-place team."""
        return self._get_loser(103)

    def get_all_results(self) -> Dict[int, Dict]:
        """Get all recorded knockout results."""
        return dict(self._results)

    def get_bracket_tree(self) -> Dict[str, Any]:
        """
        Generate the full bracket tree for visualization.

        Returns a nested dict representing the tournament bracket.
        """
        tree = {
            "tournament": "FIFA World Cup 2026",
            "format": "48-team, 12 groups → R32 → R16 → QF → SF → Final",
            "r32": [],
            "r16": [],
            "qf": [],
            "sf": [],
            "third_place": None,
            "final": None,
            "champion": self.get_champion(),
            "runner_up": self.get_runner_up(),
            "third": self.get_third_place(),
            "fourth": self.get_fourth_place(),
        }

        # R32
        for mid in R32_MATCHES:
            r = self._results.get(mid, {})
            tree["r32"].append({
                "match_id": mid,
                "home_team": r.get("home_team", "TBD"),
                "away_team": r.get("away_team", "TBD"),
                "home_goals": r.get("home_goals"),
                "away_goals": r.get("away_goals"),
                "winner": r.get("winner"),
                "extra_time": r.get("extra_time", False),
                "penalties": r.get("penalties", False),
                "penalty_score": r.get("penalty_score"),
            })

        # R16
        for mid in R16_MATCHES:
            r = self._results.get(mid, {})
            tree["r16"].append(self._match_to_tree(mid, r))

        # QF
        for mid in QF_MATCHES:
            r = self._results.get(mid, {})
            tree["qf"].append(self._match_to_tree(mid, r))

        # SF
        for mid in SF_MATCHES:
            r = self._results.get(mid, {})
            tree["sf"].append(self._match_to_tree(mid, r))

        # Third place & Final
        tree["third_place"] = self._match_to_tree(103, self._results.get(103, {}))
        tree["final"] = self._match_to_tree(104, self._results.get(104, {}))

        return tree

    def _match_to_tree(self, mid: int, r: Dict) -> Dict:
        return {
            "match_id": mid,
            "home_team": r.get("home_team", "TBD"),
            "away_team": r.get("away_team", "TBD"),
            "home_goals": r.get("home_goals"),
            "away_goals": r.get("away_goals"),
            "winner": r.get("winner"),
            "extra_time": r.get("extra_time", False),
            "penalties": r.get("penalties", False),
            "penalty_score": r.get("penalty_score"),
        }

    def validate(self) -> List[str]:
        """Validate bracket integrity."""
        issues = []

        # Check no duplicate teams in R32
        r32_teams = set()
        for mid in R32_MATCHES:
            r = self._results.get(mid)
            if r:
                for t in [r["home_team"], r["away_team"]]:
                    if t in r32_teams:
                        issues.append(f"Duplicate team in R32: {t}")
                    r32_teams.add(t)

        # Check all R32 matches have 32 unique teams
        if len(r32_teams) > 0 and len(r32_teams) != 32:
            issues.append(f"R32 has {len(r32_teams)} unique teams (expected 32)")

        # Check progression consistency
        for mid, info in R16_MATCHES.items():
            if mid in self._results:
                r = self._results[mid]
                expected_home = self._get_winner(info["home_from"])
                expected_away = self._get_winner(info["away_from"])
                if r["home_team"] != expected_home:
                    issues.append(f"M{mid}: home should be W{info['home_from']}={expected_home}, got {r['home_team']}")
                if r["away_team"] != expected_away:
                    issues.append(f"M{mid}: away should be W{info['away_from']}={expected_away}, got {r['away_team']}")

        # Check no team plays itself
        for mid, r in self._results.items():
            if r.get("home_team") == r.get("away_team") and r.get("home_team") != "TBD":
                issues.append(f"M{mid}: team plays itself: {r['home_team']}")

        return issues
