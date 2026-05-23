from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class CountryBase(BaseModel):
    name: str
    code: str = Field(..., min_length=2, max_length=3)
    confederation: str
    flag_emoji: Optional[str] = None


class CountryCreate(CountryBase):
    pass


class CountryResponse(CountryBase):
    id: str
    elo_rating: float = 1500.0
    fifa_ranking: int = 0
    attack_rating: float = 0.0
    defense_rating: float = 0.0
    form_score: float = 0.0

    class Config:
        from_attributes = True


class PredictionResponse(BaseModel):
    home_team: str
    away_team: str
    predicted_home_goals: float
    predicted_away_goals: float
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    confidence: float
    models_used: List[str] = []
    timestamp: datetime


class SimulationResponse(BaseModel):
    id: str
    iterations: int
    champion: dict
    top_4: List[dict] = []
    top_8: List[dict] = []
    timestamp: datetime


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    timestamp: datetime
