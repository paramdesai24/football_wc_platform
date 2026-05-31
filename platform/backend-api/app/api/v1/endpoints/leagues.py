from __future__ import annotations

import random
import string
import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_postgres_db
from app.models.auction_models import AuctionPlayer, League, LeagueMember, Squad

router = APIRouter(prefix="/leagues", tags=["leagues"])


def generate_invite_code() -> str:
    words = ["WOLF", "LION", "HAWK", "BULL", "TIGER", "EAGLE", "STORM", "FIRE"]
    digits = "".join(random.choices(string.digits, k=4))
    return f"{random.choice(words)}-{digits}"


class CreateLeagueRequest(BaseModel):
    name: str
    host_id: str
    budget: int = 50000
    squad_size: int = 15
    min_gk: int = 2
    min_def: int = 5
    min_mid: int = 5
    min_fwd: int = 3
    scoring_rules: Optional[Dict[str, Any]] = Field(default_factory=dict)


class JoinLeagueRequest(BaseModel):
    user_id: str
    team_name: str


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
    league = League(
        id=uuid.uuid4(),
        name=req.name,
        host_id=req.host_id,
        invite_code=generate_invite_code(),
        budget=req.budget,
        squad_size=req.squad_size,
        min_gk=req.min_gk,
        min_def=req.min_def,
        min_mid=req.min_mid,
        min_fwd=req.min_fwd,
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
    return {"squad": [{**_serialize(squad), "player": _serialize(player)} for squad, player in rows]}


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
    return {
        "leaderboard": [
            {"rank": index + 1, **_serialize(member), "squad_size": int(squad_counts.get(member.user_id, 0))}
            for index, member in enumerate(members)
        ]
    }