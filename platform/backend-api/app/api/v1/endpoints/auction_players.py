from __future__ import annotations

from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_postgres_db
from app.models.auction_models import AuctionPlayer

router = APIRouter(prefix="/auction/players", tags=["auction-players"])


def _normalized_search_expr(value):
    # Make player search tolerant of accents and common transliterations.
    source_chars = "áàäâãåÁÀÄÂÃÅéèëêÉÈËÊíìïîÍÌÏÎóòöôõÓÒÖÔÕúùüûÚÙÜÛçÇñÑ"
    target_chars = "aaaaaaAAAAAAeeeeEEEEiiiiIIIIoooooOOOOOuuuuUUUUcCnN"
    return func.lower(func.translate(value, source_chars, target_chars))


def _serialize_row(row: AuctionPlayer) -> dict[str, Any]:
    data = {key: value for key, value in row.__dict__.items() if not key.startswith("_")}
    return data


@router.get("/")
async def get_players(
    position: str | None = Query(None),
    tier: str | None = Query(None),
    iso_code: List[str] | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_postgres_db),
):
    filters = []
    if position:
        filters.append(AuctionPlayer.position == position)
    if tier:
        filters.append(AuctionPlayer.tier == tier)
    if iso_code:
        filters.append(AuctionPlayer.iso_code.in_([c.upper() for c in iso_code]))
    if search:
        normalized_search = _normalized_search_expr(func.cast(search, AuctionPlayer.name.type))
        filters.append(_normalized_search_expr(AuctionPlayer.name).like(f"%{search.lower()}%"))

    stmt = select(AuctionPlayer)
    if filters:
        stmt = stmt.where(and_(*filters))
    stmt = stmt.order_by(AuctionPlayer.market_value.desc()).limit(limit).offset(offset)

    result = await db.execute(stmt)
    players = result.scalars().all()
    return {"players": [_serialize_row(player) for player in players], "count": len(players)}


@router.get("/tiers/summary")
async def get_tier_summary(db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(AuctionPlayer.tier, func.count().label("count")).group_by(AuctionPlayer.tier))
    return {row.tier: row.count for row in result}


@router.get("/{player_id}")
async def get_player(player_id: str, db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(AuctionPlayer).where(AuctionPlayer.id == player_id))
    player = result.scalar_one_or_none()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return _serialize_row(player)