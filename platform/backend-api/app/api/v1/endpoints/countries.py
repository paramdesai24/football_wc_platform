from fastapi import APIRouter, Query
from typing import Optional
import math
import pandas as pd
from pathlib import Path

router = APIRouter()

# Load rankings data
CURRENT_FILE = Path(__file__).resolve()
# __file__ is in platform/backend-api/app/api/v1/endpoints/
# platform/data/processed is at CURRENT_FILE.parents[4] / "data" / "processed"
DATA_PATH = CURRENT_FILE.parents[4] / "data" / "processed"


def load_rankings():
    """Load rankings CSV. Ratings are used as-is (no scaling applied);
    the data pipeline is the single source of truth for calibrated values."""
    try:
        p = DATA_PATH / "dynamic_world_rankings_active.csv"
        df = pd.read_csv(p)
        return df
    except Exception as e:
        print(f"Error loading rankings: {e}")
        return pd.DataFrame()


def sanitize_records(records: list[dict]) -> list[dict]:
    """Replace any NaN / Inf float with None so json.dumps never raises."""
    cleaned = []
    for row in records:
        clean_row = {}
        for k, v in row.items():
            if isinstance(v, float) and not math.isfinite(v):
                clean_row[k] = None
            else:
                clean_row[k] = v
        cleaned.append(clean_row)
    return cleaned


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
    records = df[["country_name", "country_uid", "elo_rating", "attack_rating", "defense_rating"]].to_dict("records")
    return {
        "data": sanitize_records(records),
        "total": len(df),
        "limit": limit,
        "offset": offset,
    }


@router.get("/rankings")
async def country_rankings(
    confederation: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=40),   # hard-capped at 40 as per product spec
):
    df = load_rankings()
    if df.empty:
        return {"data": [], "total": 0}

    if confederation and confederation != "All":
        df = df[df["confederation"] == confederation]

    # Sort by the pipeline's composite weighted Smart Score (overall_rank_score),
    # falling back to elo_rating if the column is absent in older exports.
    sort_col = "overall_rank_score" if "overall_rank_score" in df.columns else "elo_rating"
    df = df.sort_values(by=sort_col, ascending=False)
    # Re-assign sequential ranks after filtering / sorting
    df["rank"] = range(1, len(df) + 1)

    df = df.head(limit)

    # Build column list — include optional columns when present
    cols = ["rank", "country_name", "country_uid", "confederation",
            "elo_rating", "attack_rating", "defense_rating", "recent_form_score"]
    if "momentum_score" in df.columns:
        cols.append("momentum_score")
    if "overall_rank_score" in df.columns:
        cols.append("overall_rank_score")

    records = df[cols].to_dict("records")
    return {
        "data": sanitize_records(records),
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

    return {"data": sanitize_records([country.iloc[0].to_dict()])[0]}
