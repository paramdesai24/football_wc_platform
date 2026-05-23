"""
Fixture Generator
===================
Generates round-robin group fixtures for FIFA World Cup 2026.
Each group of 4 teams plays 6 matches across 3 matchdays.
"""

import csv
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from itertools import combinations

from ..utils.constants import (
    TEAMS_FILE, GROUP_FIXTURES_FILE, GROUPS_FILE,
    GROUP_NAMES, TEAMS_PER_GROUP, GROUP_MATCHDAYS,
    HOST_VENUES,
)

logger = logging.getLogger("tournament.fixtures")


def load_teams() -> List[Dict]:
    """Load official WC 2026 teams from CSV."""
    teams = []
    with open(TEAMS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            teams.append(row)
    logger.info("Loaded %d qualified teams", len(teams))
    return teams


def get_groups(teams: List[Dict]) -> Dict[str, List[Dict]]:
    """Organize teams into groups."""
    groups = {}
    for team in teams:
        g = team["group"]
        if g not in groups:
            groups[g] = []
        groups[g].append(team)
    return groups


def generate_group_fixtures(teams: List[Dict]) -> List[Dict]:
    """
    Generate round-robin fixtures for all groups.

    Each group of 4 teams produces 6 matches across 3 matchdays:
    - Matchday 1: Team 1 vs Team 2, Team 3 vs Team 4
    - Matchday 2: Team 1 vs Team 3, Team 2 vs Team 4
    - Matchday 3: Team 1 vs Team 4, Team 2 vs Team 3
    """
    groups = get_groups(teams)
    fixtures = []
    match_id = 1

    for group_name in sorted(groups.keys()):
        group_teams = groups[group_name]
        # Sort by pot/seed for matchday assignment
        group_teams.sort(key=lambda t: int(t.get("pot", 4)))

        if len(group_teams) != TEAMS_PER_GROUP:
            logger.warning("Group %s has %d teams (expected %d)",
                           group_name, len(group_teams), TEAMS_PER_GROUP)

        t = [team["country_name"] for team in group_teams]
        venues = HOST_VENUES.get(group_name, [("TBD", "TBD"), ("TBD", "TBD")])

        # Standard FIFA round-robin schedule for 4 teams.
        # This covers each unique pairing exactly once.
        matchday_schedule = [
            # Matchday 1: 1v2, 3v4
            [(0, 1), (2, 3)],
            # Matchday 2: 1v3, 2v4
            [(0, 2), (1, 3)],
            # Matchday 3: 1v4, 2v3
            [(0, 3), (1, 2)],
        ]

        for md_idx, md_matches in enumerate(matchday_schedule, 1):
            for pair_idx, (h_idx, a_idx) in enumerate(md_matches):
                venue = venues[pair_idx % len(venues)]
                fixtures.append({
                    "match_id": f"GS-{match_id:03d}",
                    "group": group_name,
                    "matchday": md_idx,
                    "home_team": t[h_idx],
                    "away_team": t[a_idx],
                    "stadium": venue[0],
                    "city": venue[1],
                    "stage": "group",
                })
                match_id += 1

    logger.info("Generated %d group-stage fixtures", len(fixtures))
    return fixtures


def save_fixtures(fixtures: List[Dict], path: Path = None):
    """Save fixtures to CSV."""
    path = path or GROUP_FIXTURES_FILE
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["match_id", "group", "matchday", "home_team", "away_team",
                  "stadium", "city", "stage"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for fix in fixtures:
            writer.writerow({k: fix[k] for k in fieldnames})
    logger.info("Saved fixtures to %s", path)


def save_groups(teams: List[Dict], path: Path = None):
    """Save group composition to CSV."""
    path = path or GROUPS_FILE
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["group", "pot", "country_uid", "country_name",
                  "confederation", "fifa_ranking"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for team in sorted(teams, key=lambda t: (t["group"], int(t.get("pot", 4)))):
            writer.writerow({k: team.get(k, "") for k in fieldnames})
    logger.info("Saved group composition to %s", path)


def generate_all():
    """Generate and save all tournament fixture data."""
    teams = load_teams()
    save_groups(teams)
    fixtures = generate_group_fixtures(teams)
    save_fixtures(fixtures)
    return teams, fixtures
