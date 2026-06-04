from fastapi import APIRouter, Query
from typing import Optional
import pandas as pd
from pathlib import Path

router = APIRouter()

# Load rankings data
DATA_PATH = Path(__file__).parent.parent.parent.parent.parent / "data" / "processed"

def load_rankings():
    """Load rankings CSV. Ratings are used as-is (no scaling applied);
    the data pipeline is the single source of truth for calibrated values."""
    try:
        p = Path(r"C:\FIFA WC\platform\data\processed\dynamic_world_rankings_active.csv")
        df = pd.read_csv(p)
        return df
    except Exception as e:
        print(f"Error loading rankings: {e}")
        return pd.DataFrame()


@router.get("/")
async def list_countries(
    confederation: Optional[str] = Query(None, description="Filter by confederation"),
    sort_by: str = Query("elo_rating", description="Sort field"),
    order: str = Query("desc", description="Sort order"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    df = load_rankings()
    if df.empty:
        return {"data": [], "total": 0, "limit": limit, "offset": offset}
    
    if confederation:
        df = df[df["confederation"] == confederation]
    
    df = df.sort_values(sort_by, ascending=(order == "asc")).iloc[offset : offset + limit]
    return {
        "data": df[["country_name", "country_uid", "elo_rating", "attack_rating", "defense_rating"]].to_dict("records"),
        "total": len(df),
        "limit": limit,
        "offset": offset,
    }


@router.get("/rankings")
async def country_rankings(
    confederation: Optional[str] = Query(None),
    limit: int = Query(48, ge=1, le=200),
):
    df = load_rankings()
    if df.empty:
        return {"data": [], "total": 0}
    
    if confederation and confederation != "All":
        df = df[df["confederation"] == confederation]
    
    df = df.head(limit)
    return {
        "data": df[["rank", "country_name", "country_uid", "elo_rating", "attack_rating", "defense_rating", "recent_form_score"]].to_dict("records"),
        "total": len(df),
    }


@router.get("/{country_id}")
async def get_country(country_id: str):
    df = load_rankings()
    if df.empty:
        return {"data": None}
    
    country = df[df["country_uid"] == country_id]
    if country.empty:
        return {"data": None}
    
    return {"data": country.iloc[0].to_dict()}
