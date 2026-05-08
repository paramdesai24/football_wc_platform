from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


@router.get("/")
async def list_players(
    position: Optional[str] = Query(None, description="Filter by position"),
    country: Optional[str] = Query(None, description="Filter by country code"),
    min_form: Optional[float] = Query(None, ge=0, le=100),
    sort_by: str = Query("form_score", description="Sort field"),
    order: str = Query("desc"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return {"data": [], "total": 0, "limit": limit, "offset": offset}


@router.get("/search")
async def search_players(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=50),
):
    return {"data": [], "query": q, "total": 0}


@router.get("/country/{country_id}")
async def players_by_country(country_id: str):
    return {"data": [], "country": country_id, "total": 0}


@router.get("/{player_id}")
async def get_player(player_id: str):
    return {"data": None, "message": f"Player {player_id} detail pending data integration"}
