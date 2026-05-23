import sys
from pathlib import Path
import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

# Add project root to path for engine access
project_root = Path(r"C:\FIFA WC")
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from match_engine.probabilities.match_probability import MatchProbabilityEngine
from match_engine.utils.helpers import normalize_team_name
from app.services.prediction_history import append_prediction, get_recent_predictions

router = APIRouter()

# Initialize engine lazily
_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = MatchProbabilityEngine()
    return _engine


class PredictionRequest(BaseModel):
    home_team_id: str
    away_team_id: str
    venue: str = "neutral"
    tournament: str = "world_cup_group"



def load_rankings():
    try:
        p = Path(r"C:\FIFA WC\platform\data\processed\dynamic_world_rankings_active.csv")
        return pd.read_csv(p)
    except Exception as e:
        print(f"Error loading rankings: {e}")
        return pd.DataFrame()


@router.post("/predict")
async def predict_match(request: PredictionRequest):
    engine = get_engine()
    
    # Map UID to team name if needed
    df = load_rankings()
    home_row = df[df["country_uid"] == request.home_team_id]
    away_row = df[df["country_uid"] == request.away_team_id]
    
    if home_row.empty or away_row.empty:
        return {"data": None, "message": "Team not found"}
    
    home_name = home_row.iloc[0]["country_name"]
    away_name = away_row.iloc[0]["country_name"]
    
    try:
        result = engine.predict(
            home_name, 
            away_name, 
            venue=request.venue, 
            tournament=request.tournament
        )
        
        response = {
            "match": f"{home_name} vs {away_name}",
            "home_win_pct": round(result["home_win_prob"] * 100, 1),
            "draw_pct": round(result["draw_prob"] * 100, 1),
            "away_win_pct": round(result["away_win_prob"] * 100, 1),
            "home_xg": round(result["home_xg"], 2),
            "away_xg": round(result["away_xg"], 2),
            "predicted_score": result["predicted_score"],
            "confidence": int(result.get("confidence_score", 0.8) * 100),
            "home_team": home_name,
            "away_team": away_name,
            "explanation": result.get("explanation", "")
        }

        append_prediction({
            "match": response["match"],
            "home_team": response["home_team"],
            "away_team": response["away_team"],
            "predicted_score": response["predicted_score"],
            "home_win_pct": response["home_win_pct"],
            "draw_pct": response["draw_pct"],
            "away_win_pct": response["away_win_pct"],
            "confidence": response["confidence"],
        })

        return response
    except Exception as e:
        return {"error": str(e)}


@router.get("/history")
async def prediction_history(limit: int = 20):
    history = get_recent_predictions(limit=limit)
    return {"data": history, "total": len(history)}


@router.get("/upcoming")
async def upcoming_predictions():
    df = load_rankings()
    if df.empty or len(df) < 2:
        return {"data": []}
    
    # Sample 3 upcoming matches
    top_teams = df.head(10)
    matches = []
    for i in range(min(3, len(top_teams) - 1)):
        team1 = top_teams.iloc[i]
        team2 = top_teams.iloc[i + 1]
        elo_diff = float(team1["elo_rating"]) - float(team2["elo_rating"])
        home_prob = max(30, min(70, 50 + elo_diff / 50))
        matches.append({
            "match": f"{team1['country_uid']} vs {team2['country_uid']}",
            "home_win": f"{home_prob:.0f}%",
            "draw": f"{(100-home_prob)/2:.0f}%",
            "away_win": f"{(100-home_prob)/2:.0f}%",
        })
    
    return {"data": matches, "total": len(matches)}
