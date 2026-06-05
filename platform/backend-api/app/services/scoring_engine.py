from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auction_models import (
    AuctionPlayer,
    League,
    LeagueMember,
    LeaderboardSnapshot,
    PlayerPerformance,
    Squad,
)

DEFAULT_SCORING = {
    "goal_scored_fwd": 5,
    "goal_scored_mid": 5,
    "goal_scored_def": 6,
    "goal_scored_gk": 6,
    "assist": 3,
    "clean_sheet_def": 4,
    "clean_sheet_mid": 1,
    "clean_sheet_gk": 4,
    "yellow_card": -1,
    "red_card": -3,
    "minutes_60": 1,
    "minutes_90": 2,
    "save_3": 1,
    "penalty_saved": 5,
    "motm": 3,
    "tournament_winner": 10,
}

# Best-XI formation slots: how many players per position count toward team points
BEST_XI_SLOTS: Dict[str, int] = {
    "GK":  1,
    "DEF": 4,
    "MID": 3,
    "FWD": 3,
}


def compute_points(perf: PlayerPerformance, position: str, rules: dict) -> int:
    pts = 0
    pos = (position or "MID").upper()

    if perf.minutes_played >= 90:
        pts += rules.get("minutes_90", 2)
    elif perf.minutes_played >= 60:
        pts += rules.get("minutes_60", 1)

    goal_pos = pos.lower() if pos in {"GK", "DEF", "MID", "FWD"} else "mid"
    goal_key = f"goal_scored_{goal_pos}"
    pts += perf.goals * rules.get(goal_key, 5)

    pts += perf.assists * rules.get("assist", 3)

    if perf.clean_sheet and perf.minutes_played >= 60:
        cs_key = f"clean_sheet_{goal_pos}"
        pts += rules.get(cs_key, 0)

    pts += perf.yellow_cards * rules.get("yellow_card", -1)
    pts += perf.red_cards * rules.get("red_card", -3)

    if pos == "GK":
        pts += (perf.saves // 3) * rules.get("save_3", 1)

    return pts


def select_best_xi(user_player_points: Dict[str, List[int]]) -> int:
    """
    Given a dict of { position -> [list of points for each player at that position] },
    return the total points from the best-XI selection:
      top 1 GK + top 4 DEF + top 3 MID + top 3 FWD (by points).

    Individual player points can still be any value (including negative).
    """
    total = 0
    for pos, slots in BEST_XI_SLOTS.items():
        pts_list = sorted(user_player_points.get(pos, []), reverse=True)
        total += sum(pts_list[:slots])
    return total


async def process_match_scores(match_id: str, db: AsyncSession):
    result = await db.execute(
        select(PlayerPerformance, AuctionPlayer)
        .join(AuctionPlayer, PlayerPerformance.player_id == AuctionPlayer.id)
        .where(PlayerPerformance.match_id == match_id)
    )
    rows = result.all()

    leagues_result = await db.execute(select(League).where(League.status == "active"))
    leagues = leagues_result.scalars().all()
    if not leagues:
        await db.commit()
        return

    snapshot_result = await db.execute(select(LeaderboardSnapshot).where(LeaderboardSnapshot.match_id == match_id))
    prior_snapshots = snapshot_result.scalars().all()
    prior_points: dict[tuple[str, str], int] = defaultdict(int)
    for snapshot in prior_snapshots:
        prior_points[(str(snapshot.league_id), snapshot.user_id)] += snapshot.points_this_match or 0
        await db.delete(snapshot)

    for league in leagues:
        rules = {**DEFAULT_SCORING, **(league.scoring_rules or {})}

        # Step 1: Compute raw points for every player in this match
        player_pts: Dict[str, int] = {}     # player_id -> raw_points this match
        player_pos: Dict[str, str] = {}     # player_id -> position

        for perf, player in rows:
            pts = compute_points(perf, player.position, rules)
            perf.raw_points = pts
            player_pts[str(player.id)] = pts
            player_pos[str(player.id)] = (player.position or "MID").upper()

        # Step 2: Group players by user_id and their position -> list of points
        #         user_id -> { position -> [pts, pts, ...] }
        user_pos_points: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))

        player_ids_with_points = set(player_pts.keys())
        if player_ids_with_points:
            squad_result = await db.execute(
                select(Squad)
                .where(Squad.league_id == league.id)
                .where(Squad.player_id.in_(player_ids_with_points))
            )
            squad_entries = squad_result.scalars().all()

            for entry in squad_entries:
                pid = str(entry.player_id)
                pos = player_pos.get(pid, "MID")
                pts = player_pts.get(pid, 0)
                user_pos_points[entry.user_id][pos].append(pts)

        # Step 3: For each user, calculate team points using best-XI selection
        league_points: Dict[str, int] = {}
        for user_id, pos_map in user_pos_points.items():
            league_points[user_id] = select_best_xi(pos_map)

        affected_users = set(league_points)
        for (league_id, user_id), _points in prior_points.items():
            if league_id == str(league.id):
                affected_users.add(user_id)

        for user_id in affected_users:
            previous_points = prior_points.get((str(league.id), user_id), 0)
            current_points = league_points.get(user_id, 0)
            net_points = current_points - previous_points
            if net_points:
                await db.execute(
                    update(LeagueMember)
                    .where(LeagueMember.league_id == league.id)
                    .where(LeagueMember.user_id == user_id)
                    .values(total_points=LeagueMember.total_points + net_points)
                )

        await db.flush()

        members_result = await db.execute(
            select(LeagueMember)
            .where(LeagueMember.league_id == league.id)
            .order_by(LeagueMember.total_points.desc(), LeagueMember.joined_at.asc())
        )
        members = members_result.scalars().all()
        for rank, member in enumerate(members, 1):
            db.add(
                LeaderboardSnapshot(
                    league_id=league.id,
                    user_id=member.user_id,
                    match_id=match_id,
                    points_this_match=league_points.get(member.user_id, 0),
                    cumulative_points=member.total_points,
                    rank_at_snapshot=rank,
                )
            )

    await db.commit()