from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_postgres_db
from app.models.auction_models import AuctionPlayer, LeaderboardSnapshot, LeagueMember, PlayerPerformance, WCMatch
from app.services.scoring_engine import process_match_scores

router = APIRouter(prefix="/admin/matches", tags=["admin"])


class PlayerPerfInput(BaseModel):
    player_id: str
    goals: int = 0
    assists: int = 0
    minutes_played: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    clean_sheet: bool = False
    saves: int = 0


class MatchResultInput(BaseModel):
    match_id: str = Field(..., description='e.g. "WC2026_GS_01"')
    stage: str = Field(..., description='e.g. "Group Stage"')
    home_code: str = Field(..., description='e.g. "ESP"')
    away_code: str = Field(..., description='e.g. "FRA"')
    home_score: int
    away_score: int
    performances: List[PlayerPerfInput]


@router.post("/result")
async def submit_match_result(req: MatchResultInput, db: AsyncSession = Depends(get_postgres_db)):
    if req.performances:
        player_ids = [p.player_id for p in req.performances]
        result = await db.execute(
            select(AuctionPlayer).where(AuctionPlayer.id.in_(player_ids))
        )
        players_found = {p.id: p for p in result.scalars().all()}

        invalid = []
        home = req.home_code.upper().strip()
        away = req.away_code.upper().strip()

        for perf in req.performances:
            player = players_found.get(perf.player_id)
            if not player:
                invalid.append(f"Player ID {perf.player_id} not found in auction_players")
                continue

            player_iso = (player.iso_code or "").upper().strip()
            if player_iso not in (home, away):
                invalid.append(f"{player.name} ({player_iso}) does not play for {home} or {away}")

        if invalid:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Player-team mismatch",
                    "invalid_players": invalid,
                    "hint": f"Only players from {req.home_code} or {req.away_code} can be added to this match",
                },
            )

    match = WCMatch(
        id=req.match_id,
        stage=req.stage,
        home_code=req.home_code,
        away_code=req.away_code,
        home_score=req.home_score,
        away_score=req.away_score,
        status="completed",
    )
    await db.merge(match)

    await db.execute(delete(PlayerPerformance).where(PlayerPerformance.match_id == req.match_id))

    for perf_input in req.performances:
        db.add(
            PlayerPerformance(
                match_id=req.match_id,
                player_id=perf_input.player_id,
                goals=perf_input.goals,
                assists=perf_input.assists,
                minutes_played=perf_input.minutes_played,
                yellow_cards=perf_input.yellow_cards,
                red_cards=perf_input.red_cards,
                clean_sheet=perf_input.clean_sheet,
                saves=perf_input.saves,
            )
        )

    await db.flush()
    await process_match_scores(req.match_id, db)
    return {"status": "processed", "match_id": req.match_id}


@router.post("/recalculate")
async def recalculate_all_points(db: AsyncSession = Depends(get_postgres_db)):
    """
    Recomputes total_points for all league members from scratch.
    Use this after deleting match entries or correcting performances.
    """
    await db.execute(delete(LeaderboardSnapshot))
    await db.execute(update(LeagueMember).values(total_points=0))
    await db.commit()

    matches_result = await db.execute(
        select(WCMatch).where(WCMatch.status == "completed").order_by(WCMatch.played_at.asc(), WCMatch.id.asc())
    )
    matches = matches_result.scalars().all()

    processed: list[str] = []
    for match in matches:
      await process_match_scores(match.id, db)
      processed.append(match.id)

    return {
        "status": "recalculated",
        "matches_processed": processed,
        "count": len(processed),
    }


@router.delete("/match/{match_id}")
async def delete_match(match_id: str, db: AsyncSession = Depends(get_postgres_db)):
    """Delete a match and its performances, then recalculate all points."""
    await db.execute(delete(LeaderboardSnapshot).where(LeaderboardSnapshot.match_id == match_id))
    await db.execute(delete(PlayerPerformance).where(PlayerPerformance.match_id == match_id))
    await db.execute(delete(WCMatch).where(WCMatch.id == match_id))
    await db.execute(update(LeagueMember).values(total_points=0))
    await db.commit()

    matches_result = await db.execute(
        select(WCMatch).where(WCMatch.status == "completed").order_by(WCMatch.played_at.asc(), WCMatch.id.asc())
    )
    for match in matches_result.scalars().all():
        await process_match_scores(match.id, db)

    return {"status": "deleted_and_recalculated", "match_id": match_id}


@router.get("/")
async def list_matches(db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(WCMatch).order_by(WCMatch.played_at.desc()))
    matches = result.scalars().all()
    return {
        "matches": [
            {
                "id": match.id,
                "stage": match.stage,
                "home_code": match.home_code,
                "away_code": match.away_code,
                "home_score": match.home_score,
                "away_score": match.away_score,
                "played_at": str(match.played_at) if match.played_at else None,
                "status": match.status,
            }
            for match in matches
        ]
    }