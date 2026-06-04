from fastapi import APIRouter
import pandas as pd
from pathlib import Path

router = APIRouter()


CURRENT_FILE = Path(__file__).resolve()
# parents[5] = platform/  →  platform/data/processed
DATA_PATH = CURRENT_FILE.parents[5] / "data" / "processed"


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


def safe_float(v, default=0.0):
    try:
        import math
        f_val = float(v)
        if math.isnan(f_val) or math.isinf(f_val):
            return default
        return f_val
    except Exception:
        return default


import json

def load_breakdowns():
    """Load pre-computed component breakdowns for attack and defense."""
    try:
        with open(DATA_PATH / "attack_breakdown.json", "r", encoding="utf-8") as f:
            attack_breakdown = json.load(f)
        with open(DATA_PATH / "defense_breakdown.json", "r", encoding="utf-8") as f:
            defense_breakdown = json.load(f)
        return attack_breakdown, defense_breakdown
    except Exception as e:
        print(f"Error loading breakdowns: {e}")
        return {}, {}


@router.get("/team/{country_id}")
async def team_analytics(country_id: str):
    df = load_rankings()
    if df.empty:
        return {"data": None}
    
    team = df[df["country_uid"] == country_id]
    if team.empty:
        return {"data": None, "message": f"Team {country_id} not found"}
    
    row = team.iloc[0]
    team_name = row["country_name"]
    
    # Load detailed component breakdowns
    atk_breakdown, def_breakdown = load_breakdowns()
    
    # Lookup by country name or UID
    atk_info = atk_breakdown.get(team_name)
    if not atk_info:
        for val in atk_breakdown.values():
            if val.get("country_uid") == country_id:
                atk_info = val
                break
                
    def_info = def_breakdown.get(team_name)
    if not def_info:
        for val in def_breakdown.values():
            if val.get("country_uid") == country_id:
                def_info = val
                break
    
    atk_components = atk_info.get("components", {}) if atk_info else {}
    def_components = def_info.get("components", {}) if def_info else {}
    
    # Map to the specific detailed keys
    detailed_attack = {
        "recency_attack": safe_float(atk_components.get("recency_goals")),
        "squad_attack": safe_float(atk_components.get("squad_quality")),
        "elo_component": safe_float(atk_components.get("elo")),
        "form_component": safe_float(atk_components.get("recent_form"))
    }
    
    detailed_defense = {
        "defensive_record": safe_float(def_components.get("recency_conceded")),
        "defender_quality": safe_float(def_components.get("squad_quality")),
        "goalkeeper_quality": safe_float(def_components.get("squad_quality")),
        "clean_sheet_component": safe_float(def_components.get("recency_conceded"))
    }
    
    return {
        "country_id": country_id,
        "country_name": team_name,
        "confederation": row["confederation"],
        "elo_rating": safe_float(row["elo_rating"]),
        "attack_rating": safe_float(row["attack_rating"]),
        "defense_rating": safe_float(row["defense_rating"]),
        "recent_form": safe_float(row["recent_form_score"]),
        "squad_strength": safe_float(row["squad_overall_strength"]),
        "momentum": safe_float(row["momentum_score"]),
        "consistency": safe_float(row["consistency_score"]),
        "rank": int(row["rank"]) if pd.notna(row["rank"]) else 0,
        "power_index": safe_float(row.get("power_index")),
        "power_rank": int(row.get("power_rank")) if pd.notna(row.get("power_rank")) else 0,
        "attack_breakdown": detailed_attack,
        "defense_breakdown": detailed_defense
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
