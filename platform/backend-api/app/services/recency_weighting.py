from dataclasses import dataclass


@dataclass(frozen=True)
class FormWeights:
    recent_matches: float = 0.5
    current_season: float = 0.3
    historical_average: float = 0.2


class RecencyWeightingService:
    def __init__(self, weights: FormWeights | None = None) -> None:
        self.weights = weights or FormWeights()

    def score(self, recent_matches: float, current_season: float, historical_average: float) -> float:
        weights = self.weights
        return (
            weights.recent_matches * recent_matches
            + weights.current_season * current_season
            + weights.historical_average * historical_average
        )


def normalize_score(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    if maximum <= minimum:
        return 0.0
    clipped = max(min(value, maximum), minimum)
    return (clipped - minimum) / (maximum - minimum)
