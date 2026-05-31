from __future__ import annotations

from collections import defaultdict

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
        league_points: dict[str, int] = defaultdict(int)

        for perf, player in rows:
            pts = compute_points(perf, player.position, rules)
            perf.raw_points = pts

            squad_result = await db.execute(
                select(Squad)
                .where(Squad.league_id == league.id)
                .where(Squad.player_id == player.id)
            )
            squad_entry = squad_result.scalar_one_or_none()
            if squad_entry:
                league_points[squad_entry.user_id] += pts

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