from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_postgres_db
from app.models.auction_models import AuctionSession, League

router = APIRouter(prefix="/rooms", tags=["rooms"])


class CreateRoomRequest(BaseModel):
    league_id: str


def _serialize(obj):
    return {key: value for key, value in obj.__dict__.items() if not key.startswith("_")}


@router.post("/")
async def create_room(req: CreateRoomRequest, db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(League).where(League.id == uuid.UUID(req.league_id)))
    league = result.scalar_one_or_none()
    if not league:
        raise HTTPException(status_code=404, detail="League not found")

    room = AuctionSession(league_id=league.id, status="waiting")
    db.add(room)
    await db.commit()
    return {"room_id": str(room.id), "league_id": str(league.id), "status": room.status}


@router.get("/{league_id}")
async def get_room(league_id: str, db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(AuctionSession).where(AuctionSession.league_id == uuid.UUID(league_id)))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return _serialize(room)


@router.post("/{league_id}/start")
async def start_room(league_id: str, db: AsyncSession = Depends(get_postgres_db)):
    result = await db.execute(select(AuctionSession).where(AuctionSession.league_id == uuid.UUID(league_id)))
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    room.status = "live"
    await db.commit()
    return {"room_id": str(room.id), "status": room.status}