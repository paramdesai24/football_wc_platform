from dataclasses import dataclass
from math import exp, factorial

from app.schemas.common import ExpectedGoals, MatchPredictionRequest, MatchPredictionResponse, WinProbabilities
from app.services.recency_weighting import RecencyWeightingService


@dataclass(frozen=True)
class TeamFeatureVector:
    elo: float
    attack: float
    defense: float
    recent_form: float
    squad_form: float
    player_form_bias: float


class PredictionService:
    def __init__(self, weighting_service: RecencyWeightingService | None = None) -> None:
        self.weighting_service = weighting_service or RecencyWeightingService()

    def build_feature_vector(self, team_strength: TeamFeatureVector) -> float:
        form_bias = self.weighting_service.score(
            team_strength.recent_form,
            team_strength.squad_form,
            team_strength.player_form_bias,
        )
        return 0.35 * team_strength.attack + 0.25 * team_strength.defense + 0.25 * team_strength.elo / 100.0 + 0.15 * form_bias

    def expected_goals(self, home_strength: TeamFeatureVector, away_strength: TeamFeatureVector, neutral_venue: bool) -> ExpectedGoals:
        home_signal = self.build_feature_vector(home_strength)
        away_signal = self.build_feature_vector(away_strength)
        venue_adjustment = 0.08 if not neutral_venue else 0.0
        home_xg = max(0.2, 1.2 + home_signal - 0.75 * away_strength.defense + venue_adjustment)
        away_xg = max(0.2, 1.0 + away_signal - 0.75 * home_strength.defense)
        return ExpectedGoals(home=round(home_xg, 2), away=round(away_xg, 2))

    def score_probability(self, lambda_value: float, goals: int) -> float:
        return exp(-lambda_value) * (lambda_value**goals) / factorial(goals)

    def predict(self, request: MatchPredictionRequest) -> MatchPredictionResponse:
        # Production implementation will hydrate team vectors from country, squad, and player-form services.
        home_strength = TeamFeatureVector(elo=1625, attack=0.74, defense=0.67, recent_form=0.72, squad_form=0.76, player_form_bias=0.81)
        away_strength = TeamFeatureVector(elo=1585, attack=0.70, defense=0.68, recent_form=0.69, squad_form=0.71, player_form_bias=0.75)

        expected_goals = self.expected_goals(home_strength, away_strength, request.neutral_venue)
        home_win = max(0.05, min(0.75, 0.38 + (expected_goals.home - expected_goals.away) * 0.12))
        away_win = max(0.05, min(0.75, 0.28 + (expected_goals.away - expected_goals.home) * 0.10))
        draw = max(0.10, round(1.0 - home_win - away_win, 2))
        scale = home_win + draw + away_win
        probabilities = WinProbabilities(home=round(home_win / scale, 2), draw=round(draw / scale, 2), away=round(away_win / scale, 2))

        predicted_score_home = max(0, round(expected_goals.home))
        predicted_score_away = max(0, round(expected_goals.away))

        confidence = round(min(0.97, 0.55 + abs(expected_goals.home - expected_goals.away) * 0.08), 2)

        return MatchPredictionResponse(
            home_team=request.home_team,
            away_team=request.away_team,
            predicted_score_home=predicted_score_home,
            predicted_score_away=predicted_score_away,
            win_probabilities=probabilities,
            expected_goals=expected_goals,
            confidence=confidence,
        )
