from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


@router.get("/")
async def list_countries(
    confederation: Optional[str] = Query(None, description="Filter by confederation"),
    sort_by: str = Query("elo_rating", description="Sort field"),
    order: str = Query("desc", description="Sort order"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return {
        "data": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
        "message": "Country data will be available after data pipeline integration",
    }


@router.get("/rankings")
async def country_rankings(
    confederation: Optional[str] = Query(None),
    limit: int = Query(48, ge=1, le=200),
):
    return {
        "data": [],
        "total": 0,
        "message": "Rankings will be computed from Elo ratings engine",
    }


@router.get("/{country_id}")
async def get_country(country_id: str):
    return {
        "data": None,
        "message": f"Country detail for {country_id} will be available after data integration",
    }
