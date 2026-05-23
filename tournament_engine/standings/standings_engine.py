"""
FIFA Standings Engine
========================
Implements official FIFA World Cup group standings with proper tiebreakers.

Tiebreaker order:
1. Points
2. Goal difference
3. Goals scored
4. Head-to-head points
5. Head-to-head goal difference
6. Head-to-head goals scored
7. Fair play (yellow/red cards — simplified)
8. Drawing of lots (random)
"""

import logging
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import random

from ..utils.constants import (
    POINTS_WIN, POINTS_DRAW, POINTS_LOSS,
    AUTO_ADVANCE, BEST_THIRD,
)

logger = logging.getLogger("tournament.standings")


class StandingsEngine:
    """
    Manages group standings with full FIFA tiebreaker resolution.
    """

    def __init__(self):
        self._standings: Dict[str, Dict[str, Dict]] = {}  # group -> team -> stats
        self._match_results: List[Dict] = []

    def reset(self):
        """Reset all standings."""
        self._standings = {}
        self._match_results = []

    def initialize_group(self, group: str, teams: List[str]):
        """Initialize standings for a group."""
        self._standings[group] = {}
        for team in teams:
            self._standings[group][team] = {
                "team": team,
                "group": group,
                "played": 0,
                "won": 0,
                "drawn": 0,
                "lost": 0,
                "goals_for": 0,
                "goals_against": 0,
                "goal_difference": 0,
                "points": 0,
                "position": 0,
            }

    def update_from_match(self, result: Dict[str, Any]):
        """Update standings from a match result."""
        group = result["group"]
        home = result["home_team"]
        away = result["away_team"]
        hg = result["home_goals"]
        ag = result["away_goals"]

        if group not in self._standings:
            self.initialize_group(group, [home, away])

        for team in [home, away]:
            if team not in self._standings[group]:
                self._standings[group][team] = {
                    "team": team, "group": group,
                    "played": 0, "won": 0, "drawn": 0, "lost": 0,
                    "goals_for": 0, "goals_against": 0,
                    "goal_difference": 0, "points": 0, "position": 0,
                }

        # Update home team
        hs = self._standings[group][home]
        hs["played"] += 1
        hs["goals_for"] += hg
        hs["goals_against"] += ag

        # Update away team
        as_ = self._standings[group][away]
        as_["played"] += 1
        as_["goals_for"] += ag
        as_["goals_against"] += hg

        if hg > ag:
            hs["won"] += 1; hs["points"] += POINTS_WIN
            as_["lost"] += 1; as_["points"] += POINTS_LOSS
        elif ag > hg:
            as_["won"] += 1; as_["points"] += POINTS_WIN
            hs["lost"] += 1; hs["points"] += POINTS_LOSS
        else:
            hs["drawn"] += 1; hs["points"] += POINTS_DRAW
            as_["drawn"] += 1; as_["points"] += POINTS_DRAW

        hs["goal_difference"] = hs["goals_for"] - hs["goals_against"]
        as_["goal_difference"] = as_["goals_for"] - as_["goals_against"]

        self._match_results.append(result)

    def update_from_results(self, results: List[Dict]):
        """Update standings from multiple match results."""
        for result in results:
            self.update_from_match(result)

    def get_group_standings(self, group: str) -> List[Dict]:
        """Get sorted standings for a group with FIFA tiebreakers applied."""
        if group not in self._standings:
            return []

        teams = list(self._standings[group].values())
        group_matches = [r for r in self._match_results if r["group"] == group]

        # Sort using FIFA tiebreaker chain
        sorted_teams = self._sort_with_tiebreakers(teams, group_matches)

        # Assign positions
        for i, team in enumerate(sorted_teams):
            team["position"] = i + 1

        return sorted_teams

    def get_all_standings(self) -> Dict[str, List[Dict]]:
        """Get sorted standings for all groups."""
        result = {}
        for group in sorted(self._standings.keys()):
            result[group] = self.get_group_standings(group)
        return result

    def get_advancing_teams(self) -> Dict[str, List[Dict]]:
        """
        Determine which teams advance to the knockout stage.

        Returns dict with:
        - "group_winners": List of 12 group winners (1st place)
        - "group_runners": List of 12 runners-up (2nd place)
        - "best_thirds": List of 8 best 3rd-place teams
        - "all_advancing": Combined list of all 32 advancing teams
        """
        all_standings = self.get_all_standings()

        winners = []
        runners = []
        all_thirds = []

        for group, standings in all_standings.items():
            if len(standings) >= 1:
                winners.append(standings[0])
            if len(standings) >= 2:
                runners.append(standings[1])
            if len(standings) >= 3:
                thirds = standings[2].copy()
                thirds["source_group"] = group
                all_thirds.append(thirds)

        # Determine best 8 third-place teams
        best_thirds = self._rank_third_place_teams(all_thirds)

        return {
            "group_winners": winners,
            "group_runners": runners,
            "best_thirds": best_thirds,
            "all_advancing": winners + runners + best_thirds,
            "eliminated_thirds": all_thirds[BEST_THIRD:] if len(all_thirds) > BEST_THIRD else [],
            "fourths": [s[3] for g, s in all_standings.items() if len(s) >= 4],
        }

    def _sort_with_tiebreakers(self, teams: List[Dict],
                                group_matches: List[Dict]) -> List[Dict]:
        """Sort teams using the full FIFA tiebreaker chain."""
        import functools

        def compare(a, b):
            # 1. Points (higher first)
            if a["points"] != b["points"]:
                return b["points"] - a["points"]

            # 2. Goal difference (higher first)
            if a["goal_difference"] != b["goal_difference"]:
                return b["goal_difference"] - a["goal_difference"]

            # 3. Goals scored (higher first)
            if a["goals_for"] != b["goals_for"]:
                return b["goals_for"] - a["goals_for"]

            # 4-6. Head-to-head
            h2h = self._head_to_head(a["team"], b["team"], group_matches)
            if h2h != 0:
                return h2h

            # 7. Fair play (random tiebreak as simplified proxy)
            return random.choice([-1, 1])

        return sorted(teams, key=functools.cmp_to_key(compare))

    def _head_to_head(self, team_a: str, team_b: str,
                       matches: List[Dict]) -> int:
        """
        Head-to-head comparison between two teams.
        Returns negative if team_a is better, positive if team_b.
        """
        h2h_matches = [
            m for m in matches
            if (m["home_team"] == team_a and m["away_team"] == team_b) or
               (m["home_team"] == team_b and m["away_team"] == team_a)
        ]

        if not h2h_matches:
            return 0

        a_pts = 0
        b_pts = 0
        a_gf = 0
        b_gf = 0

        for m in h2h_matches:
            if m["home_team"] == team_a:
                a_gf += m["home_goals"]
                b_gf += m["away_goals"]
                if m["home_goals"] > m["away_goals"]:
                    a_pts += 3
                elif m["home_goals"] == m["away_goals"]:
                    a_pts += 1; b_pts += 1
                else:
                    b_pts += 3
            else:
                b_gf += m["home_goals"]
                a_gf += m["away_goals"]
                if m["home_goals"] > m["away_goals"]:
                    b_pts += 3
                elif m["home_goals"] == m["away_goals"]:
                    a_pts += 1; b_pts += 1
                else:
                    a_pts += 3

        # H2H points
        if a_pts != b_pts:
            return b_pts - a_pts

        # H2H goal difference
        a_gd = a_gf - b_gf
        b_gd = b_gf - a_gf
        if a_gd != b_gd:
            return b_gd - a_gd

        # H2H goals scored
        if a_gf != b_gf:
            return b_gf - a_gf

        return 0

    def _rank_third_place_teams(self, thirds: List[Dict]) -> List[Dict]:
        """Rank all 3rd-place teams and return the best 8."""
        # Sort by: points, GD, GF, then fair play
        thirds.sort(key=lambda t: (
            -t["points"],
            -t["goal_difference"],
            -t["goals_for"],
            t.get("goals_against", 0),
        ))
        return thirds[:BEST_THIRD]

    def format_standings_table(self, group: str) -> str:
        """Format standings as a readable table."""
        standings = self.get_group_standings(group)
        lines = [f"Group {group}:"]
        lines.append(f"{'Pos':>3} {'Team':<25} {'Pld':>3} {'W':>2} {'D':>2} {'L':>2} {'GF':>3} {'GA':>3} {'GD':>4} {'Pts':>3}")
        lines.append("-" * 60)
        for s in standings:
            lines.append(
                f"{s['position']:>3} {s['team']:<25} {s['played']:>3} "
                f"{s['won']:>2} {s['drawn']:>2} {s['lost']:>2} "
                f"{s['goals_for']:>3} {s['goals_against']:>3} "
                f"{s['goal_difference']:>+4d} {s['points']:>3}"
            )
        return "\n".join(lines)
