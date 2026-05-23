from pydantic import BaseModel, Field


class MatchPredictionRequest(BaseModel):
    home_team: str = Field(min_length=1)
    away_team: str = Field(min_length=1)
    tournament_stage: str | None = None
    neutral_venue: bool = True


class WinProbabilities(BaseModel):
    home: float
    draw: float
    away: float


class ExpectedGoals(BaseModel):
    home: float
    away: float


class MatchPredictionResponse(BaseModel):
    home_team: str
    away_team: str
    predicted_score_home: int
    predicted_score_away: int
    win_probabilities: WinProbabilities
    expected_goals: ExpectedGoals
    confidence: float
