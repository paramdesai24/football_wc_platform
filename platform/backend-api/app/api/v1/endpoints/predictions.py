from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class PredictionRequest(BaseModel):
    home_team_id: str
    away_team_id: str
    venue: str | None = None
    neutral_ground: bool = False


@router.post("/predict")
async def predict_match(request: PredictionRequest):
    return {
        "data": None,
        "message": "Prediction engine integration pending (Elo + Poisson + XGBoost)",
        "request": request.model_dump(),
    }


@router.get("/history")
async def prediction_history(limit: int = 20):
    return {"data": [], "total": 0}


@router.get("/upcoming")
async def upcoming_predictions():
    return {"data": [], "total": 0}
