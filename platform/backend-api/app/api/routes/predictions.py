from fastapi import APIRouter

from app.schemas.common import MatchPredictionRequest, MatchPredictionResponse
from app.services.prediction_service import PredictionService

router = APIRouter()
prediction_service = PredictionService()


@router.post("/match", response_model=MatchPredictionResponse)
def predict_match(request: MatchPredictionRequest) -> MatchPredictionResponse:
    return prediction_service.predict(request)
