from fastapi import APIRouter
import pandas as pd
from pathlib import Path

router = APIRouter()


def load_rankings():
    try:
        p = Path(r"C:\FIFA WC\platform\data\processed\dynamic_world_rankings_active.csv")
        return pd.read_csv(p)
    except Exception as e:
        print(f"Error loading rankings: {e}")
        return pd.DataFrame()


@router.get("/team/{country_id}")
async def team_analytics(country_id: str):
    df = load_rankings()
    if df.empty:
        return {"data": None}
    
    team = df[df["country_uid"] == country_id]
    if team.empty:
        return {"data": None, "message": f"Team {country_id} not found"}
    
    row = team.iloc[0]
    return {
        "country_id": country_id,
        "country_name": row["country_name"],
        "confederation": row["confederation"],
        "elo_rating": float(row["elo_rating"]),
        "attack_rating": float(row["attack_rating"]),
        "defense_rating": float(row["defense_rating"]),
        "recent_form": float(row["recent_form_score"]),
        "squad_strength": float(row["squad_overall_strength"]),
        "momentum": float(row["momentum_score"]),
        "consistency": float(row["consistency_score"]),
        "rank": int(row["rank"]),
    }


@router.get("/compare")
async def compare_teams(team_ids: str = ""):
    ids = [t.strip() for t in team_ids.split(",") if t.strip()]
    df = load_rankings()
    if df.empty:
        return {"data": [], "teams": ids}
    
    comparison = []
    for tid in ids:
        team = df[df["country_uid"] == tid]
        if not team.empty:
            row = team.iloc[0]
            comparison.append({
                "country_id": tid,
                "country_name": row["country_name"],
                "elo": float(row["elo_rating"]),
                "attack": float(row["attack_rating"]),
                "defense": float(row["defense_rating"]),
            })
    
    return {"data": comparison, "teams": ids, "total": len(comparison)}


@router.get("/trends/{country_id}")
async def team_trends(country_id: str, months: int = 12):
    df = load_rankings()
    team = df[df["country_uid"] == country_id]
    if team.empty:
        return {"data": None}
    
    row = team.iloc[0]
    return {
        "country_id": country_id,
        "period_months": months,
        "current_elo": float(row["elo_rating"]),
        "momentum": float(row["momentum_score"]),
        "form_trend": "up" if row["momentum_score"] > 0 else "down" if row["momentum_score"] < 0 else "stable",
    }
