from __future__ import annotations

import random
import string
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_postgres_db
from app.models.auction_models import AuctionPlayer, League, LeaderboardSnapshot, LeagueMember, PlayerPerformance, Squad

router = APIRouter(prefix="/leagues", tags=["leagues"])


def generate_invite_code() -> str:
    words = ["WOLF", "LION", "HAWK", "BULL", "TIGER", "EAGLE", "STORM", "FIRE"]
    digits = "".join(random.choices(string.digits, k=4))
    return f"{random.choice(words)}-{digits}"


class CreateLeagueRequest(BaseModel):
    name: str
    host_id: str
    budget: int = 50000
    squad_size: int = 20
    min_gk: int = 3
    min_def: int = 5
    min_mid: int = 5
    min_fwd: int = 5
    max_gk: int = 3
    max_def: int = 7
    max_mid: int = 7
    max_fwd: int = 7
    scoring_rules: Optional[Dict[str, Any]] = Field(default_factory=dict)


class JoinLeagueRequest(BaseModel):
    user_id: str
    team_name: str


class RejoinLeagueRequest(BaseModel):
    user_id: str


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


@router.get("/")
async def list_leagues(db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(League).order_by(League.created_at.desc()))
    leagues = result.scalars().all()
    return {
        "leagues": [
            {
                "id": str(l.id),
                "name": l.name,
                "invite_code": l.invite_code,
                "status": l.status,
                "budget": l.budget,
                "host_id": l.host_id,
                "created_at": str(l.created_at),
            }
            for l in leagues
        ]
    }


def _serialize(obj: Any) -> dict[str, Any]:
    return {key: value for key, value in obj.__dict__.items() if not key.startswith("_")}


@router.post("/")
async def create_league(req: CreateLeagueRequest, db: AsyncSession = Depends(get_postgres_db)):
    scoring = {**DEFAULT_SCORING, **req.scoring_rules}

    # Scale requirements dynamically: default rules for S=20 are 3 GK, 5 DEF, 5 MID, 5 FWD.
    # Every 1 increase in squad size above 20 increases min defenders requirement by 1.
    squad_size = req.squad_size
    diff = max(0, squad_size - 20)

    min_gk = req.min_gk
    min_def = req.min_def + diff
    min_mid = req.min_mid
    min_fwd = req.min_fwd

    max_gk = max(min_gk, req.max_gk)
    max_def = max(min_def, req.max_def + diff)
    max_mid = max(min_mid, req.max_mid)
    max_fwd = max(min_fwd, req.max_fwd)

    league = League(
        id=uuid.uuid4(),
        name=req.name,
        host_id=req.host_id,
        invite_code=generate_invite_code(),
        budget=req.budget,
        squad_size=req.squad_size,
        min_gk=min_gk,
        min_def=min_def,
        min_mid=min_mid,
        min_fwd=min_fwd,
        max_gk=max_gk,
        max_def=max_def,
        max_mid=max_mid,
        max_fwd=max_fwd,
        scoring_rules=scoring,
    )
    db.add(league)
    await db.commit()
    return {"league_id": str(league.id), "invite_code": league.invite_code}


@router.post("/{invite_code}/join")
async def join_league(invite_code: str, req: JoinLeagueRequest, db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(League).where(League.invite_code == invite_code.upper()))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    if league.status != "auction":
        raise HTTPException(status_code=400, detail="League auction already started")

    db.add(
        LeagueMember(
            league_id=league.id,
            user_id=req.user_id,
            team_name=req.team_name,
            budget_left=league.budget,
        )
    )
    await db.commit()
    return {"joined": True, "league_id": str(league.id), "budget": league.budget}


@router.post("/{invite_code}/rejoin")
async def rejoin_league(invite_code: str, req: RejoinLeagueRequest, db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(League).where(func.upper(League.invite_code) == invite_code.upper()))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    member_result = await db.execute(
        select(LeagueMember)
        .where(LeagueMember.league_id == league.id)
        .where(LeagueMember.user_id == req.user_id)
    )
    member = member_result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="You are not a registered member of this league. Please join first.")

    return {
        "joined": True,
        "league_id": str(league.id),
        "team_name": member.team_name,
        "budget": league.budget,
    }



@router.get("/my")
async def my_leagues(user_id: str = Query(...), db: AsyncSession = Depends(get_postgres_db)):
    """Get all leagues where user_id (email) is a member."""
    result = await db.execute(
        select(League, LeagueMember)
        .join(LeagueMember, League.id == LeagueMember.league_id)
        .where(LeagueMember.user_id == user_id)
        .order_by(League.created_at.desc())
    )
    rows = result.all()
    return {
        "leagues": [
            {
                "id":               str(league.id),
                "name":             league.name,
                "invite_code":      league.invite_code,
                "status":           league.status,
                "host_id":          league.host_id,
                "budget":           league.budget,
                "my_budget_left":   member.budget_left,
                "my_budget_spent":  member.budget_spent,
                "my_total_points":  member.total_points,
                "my_team_name":     member.team_name,
                "created_at":       str(league.created_at),
            }
            for league, member in rows
        ]
    }


@router.get("/{league_id}")
async def get_league(league_id: str, db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(League).where(League.id == uuid.UUID(league_id)))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    members_result = await db.execute(select(LeagueMember).where(LeagueMember.league_id == league.id))
    members = members_result.scalars().all()
    squad_counts_result = await db.execute(
        select(Squad.user_id, func.count(Squad.id))
        .where(Squad.league_id == league.id)
        .group_by(Squad.user_id)
    )
    squad_counts = {user_id: count for user_id, count in squad_counts_result.all()}
    serialized_members = []
    for member in members:
        member_data = _serialize(member)
        member_data["squad_count"] = int(squad_counts.get(member.user_id, 0))
        serialized_members.append(member_data)

    return {"league": _serialize(league), "members": serialized_members, "member_count": len(members)}


@router.get("/{league_id}/squad/{user_id}")
async def get_squad(league_id: str, user_id: str, db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(
        select(Squad, AuctionPlayer)
        .join(AuctionPlayer, Squad.player_id == AuctionPlayer.id)
        .where(Squad.league_id == uuid.UUID(league_id))
        .where(Squad.user_id == user_id)
    )
    rows = result.all()

    # Aggregate total raw_points per player across all matches
    player_ids = [str(player.id) for _, player in rows]
    player_total_pts: dict[str, int] = {}
    if player_ids:
        pts_result = await db.execute(
            select(PlayerPerformance.player_id, func.sum(PlayerPerformance.raw_points))
            .where(PlayerPerformance.player_id.in_(player_ids))
            .group_by(PlayerPerformance.player_id)
        )
        player_total_pts = {str(pid): int(total or 0) for pid, total in pts_result.all()}

    # Compute best-XI per position: top 1 GK, 4 DEF, 3 MID, 3 FWD
    BEST_XI_SLOTS = {"GK": 1, "DEF": 4, "MID": 3, "FWD": 3}
    pos_groups: dict[str, list[tuple[str, int]]] = {"GK": [], "DEF": [], "MID": [], "FWD": []}
    for _, player in rows:
        pos = (player.position or "MID").upper()
        pts = player_total_pts.get(str(player.id), 0)
        if pos in pos_groups:
            pos_groups[pos].append((str(player.id), pts))

    in_best_xi: set[str] = set()
    for pos, slot_count in BEST_XI_SLOTS.items():
        sorted_players = sorted(pos_groups.get(pos, []), key=lambda x: x[1], reverse=True)
        for pid, _ in sorted_players[:slot_count]:
            in_best_xi.add(pid)

    squad_data = []
    for squad, player in rows:
        entry = {**_serialize(squad), "player": _serialize(player)}
        pid = str(player.id)
        entry["player_total_points"] = player_total_pts.get(pid, 0)
        entry["in_best_xi"] = pid in in_best_xi
        squad_data.append(entry)

    return {"squad": squad_data}


@router.get("/{league_id}/leaderboard")
async def get_leaderboard(league_id: str, db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(
        select(LeagueMember)
        .where(LeagueMember.league_id == uuid.UUID(league_id))
        .order_by(LeagueMember.total_points.desc())
    )
    members = result.scalars().all()
    squad_counts_result = await db.execute(
        select(Squad.user_id, func.count(Squad.id))
        .where(Squad.league_id == uuid.UUID(league_id))
        .group_by(Squad.user_id)
    )
    squad_counts = {user_id: count for user_id, count in squad_counts_result.all()}

    # ── Rank movement: compare two most-recent snapshot timestamps ──────────
    # Get the two most recent distinct snapshot timestamps for this league
    ts_result = await db.execute(
        select(LeaderboardSnapshot.snapshot_at)
        .where(LeaderboardSnapshot.league_id == uuid.UUID(league_id))
        .distinct()
        .order_by(LeaderboardSnapshot.snapshot_at.desc())
        .limit(2)
    )
    timestamps = [row[0] for row in ts_result.all()]

    # Maps: user_id -> rank at each snapshot
    latest_ranks: dict[str, int] = {}
    previous_ranks: dict[str, int] = {}

    if timestamps:
        latest_ts = timestamps[0]
        snap_latest = await db.execute(
            select(LeaderboardSnapshot.user_id, LeaderboardSnapshot.rank_at_snapshot)
            .where(LeaderboardSnapshot.league_id == uuid.UUID(league_id))
            .where(LeaderboardSnapshot.snapshot_at == latest_ts)
        )
        latest_ranks = {row[0]: row[1] for row in snap_latest.all()}

    if len(timestamps) >= 2:
        prev_ts = timestamps[1]
        snap_prev = await db.execute(
            select(LeaderboardSnapshot.user_id, LeaderboardSnapshot.rank_at_snapshot)
            .where(LeaderboardSnapshot.league_id == uuid.UUID(league_id))
            .where(LeaderboardSnapshot.snapshot_at == prev_ts)
        )
        previous_ranks = {row[0]: row[1] for row in snap_prev.all()}

    rows = []
    for index, member in enumerate(members):
        current_rank = index + 1
        latest_snap_rank  = latest_ranks.get(member.user_id)
        prev_snap_rank    = previous_ranks.get(member.user_id)

        if latest_snap_rank is not None and prev_snap_rank is not None:
            # positive = moved up (lower rank number is better)
            rank_change = prev_snap_rank - latest_snap_rank
        else:
            rank_change = None  # no history yet

        rows.append({
            "rank":         current_rank,
            "rank_change":  rank_change,
            **_serialize(member),
            "squad_size":   int(squad_counts.get(member.user_id, 0)),
        })

    return {"leaderboard": rows}