"""
Match Probability Engine — v2.0
=================================
Orchestrates winner prediction, expected goals, and Poisson scoring
into a unified match probability output.

v2 changes:
- Reduced Poisson blend weight for draws
- Context-aware scoreline from Poisson model
- Tactical profile pass-through

v2.1 changes:
- Team identity persistence for offensive/defensive ratings
- Form modifier and consistency factor integration
- Fatigue tracking for tournament matches

v2.2 changes:
- Realism constraints for upset caps and elite defense suppression
- Low blowout probability caps
"""

import logging
from typing import Dict, Any, Optional

from ..utils.data_loader import IntelligenceDataLoader
from ..utils.helpers import normalize_team_name
from ..team_identity import TeamIdentityEngine
from ..realism_constraints import RealismConstraintsEngine
from ..winner_prediction.predictor import WinnerPredictor
from ..score_prediction.expected_goals import ExpectedGoalsEngine
from ..score_prediction.poisson_model import PoissonScoreModel

logger = logging.getLogger("match_engine.match_probability")


class MatchProbabilityEngine:
    """
    Unified match prediction engine combining all intelligence signals.

    Includes team identity persistence metrics and realism constraints
    to improve prediction consistency based on offensive/defensive ratings,
    form, and to prevent unrealistic probabilities.

    Usage:
        engine = MatchProbabilityEngine()
        result = engine.predict("France", "Brazil")
    """

    def __init__(self, data_loader: Optional[IntelligenceDataLoader] = None):
        self._loader = data_loader or IntelligenceDataLoader()
        if not self._loader._loaded:
            self._loader.load_all()
        self._winner = WinnerPredictor(self._loader.league_averages)
        self._xg = ExpectedGoalsEngine(self._loader.league_averages)
        self._poisson = PoissonScoreModel()
        self._identity = TeamIdentityEngine()
        self._realism = RealismConstraintsEngine()

    def predict(
        self,
        home_team_name: str,
        away_team_name: str,
        venue: str = "neutral",
        tournament: str = "friendly",
        home_data: Optional[Dict[str, Any]] = None,
        away_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate a complete match prediction with team identity persistence.

        Returns complete prediction dict with winner, xG, scoreline, probabilities,
        and team identity metrics (offensive/defensive ratings, form, consistency).
        """
        # Resolve team names
        h_key = normalize_team_name(home_team_name)
        a_key = normalize_team_name(away_team_name)

        home = home_data or self._loader.get_team(h_key)
        away = away_data or self._loader.get_team(a_key)

        if home is None:
            raise ValueError(f"Team not found: '{home_team_name}' (tried '{h_key}')")
        if away is None:
            raise ValueError(f"Team not found: '{away_team_name}' (tried '{a_key}')")

        # Enrich team data with identity persistence metrics
        home = self._identity.enrich_team_data(home)
        away = self._identity.enrich_team_data(away)

        h_name = home.get("country_name", home_team_name)
        a_name = away.get("country_name", away_team_name)

        # 1. Winner prediction
        winner_result = self._winner.predict(home, away, venue, tournament)

        # 2. Expected goals
        xg_result = self._xg.compute(home, away, venue, tournament)

        # 3. Poisson scoreline prediction
        score_result = self._poisson.predict(
            xg_result["home_xg"], xg_result["away_xg"], h_name, a_name
        )

        # 4. Blend Poisson outcome probs with winner prediction
        blended = self._blend_probabilities(winner_result, score_result)

        # 5. Build prediction dictionary before constraint application
        prediction = {
            "home_team": h_name,
            "away_team": a_name,
            "venue": venue,
            "tournament": tournament,
            # Winner prediction
            "predicted_winner": winner_result["predicted_winner"],
            "home_win_prob": blended["home_win"],
            "draw_prob": blended["draw"],
            "away_win_prob": blended["away_win"],
            # Expected goals
            "home_xg": xg_result["home_xg"],
            "away_xg": xg_result["away_xg"],
            "total_xg": xg_result["total_xg"],
            # Scoreline
            "predicted_score": score_result["predicted_score"],
            "predicted_home_goals": score_result["home_goals"],
            "predicted_away_goals": score_result["away_goals"],
            "score_probability": score_result["score_probability"],
            "top_scorelines": score_result["top_scorelines"][:5],
            # Markets
            "markets": score_result["markets"],
            # Raw contributions for explainability
            "contributions": winner_result["contributions"],
            "xg_factors": {
                "home": xg_result["home_factors"],
                "away": xg_result["away_factors"],
            },
            # Tactical info (v2)
            "home_tactical": xg_result.get("home_tactical", {}),
            "away_tactical": xg_result.get("away_tactical", {}),
            # Team identity persistence (v2.1)
            "home_identity": {
                "offensive_rating": home.get("offensive_rating"),
                "defensive_rating": home.get("defensive_rating"),
                "form_modifier": home.get("form_modifier"),
                "consistency_factor": home.get("consistency_factor"),
                "fatigue_factor": home.get("fatigue_factor", 1.0),
            },
            "away_identity": {
                "offensive_rating": away.get("offensive_rating"),
                "defensive_rating": away.get("defensive_rating"),
                "form_modifier": away.get("form_modifier"),
                "consistency_factor": away.get("consistency_factor"),
                "fatigue_factor": away.get("fatigue_factor", 1.0),
            },
        }

        # 6. Apply realism constraints (v2.2)
        prediction = self._realism.apply_constraints(prediction, home, away)

        return prediction

    def predict_batch(
        self,
        matchups: list,
        venue: str = "neutral",
        tournament: str = "friendly",
    ) -> list:
        """Predict multiple matches."""
        results = []
        for home, away in matchups:
            try:
                result = self.predict(home, away, venue, tournament)
                results.append(result)
            except ValueError as e:
                logger.warning("Skipping match: %s", e)
        return results

    def _blend_probabilities(
        self, winner: Dict, score: Dict
    ) -> Dict[str, float]:
        """
        Blend winner prediction probs (intelligence-based) with
        Poisson-derived probs (score-model-based).

        v2: Increased intelligence weight to 60/40 and apply
        draw dampening when Poisson draw is unrealistically high.
        """
        w_intel = 0.60  # Weight for intelligence-based prediction
        w_score = 0.40  # Weight for score-model prediction

        poisson_probs = score.get("outcome_probs", {})

        home = w_intel * winner["home_win_prob"] + w_score * poisson_probs.get("home_win", 0.33)
        draw = w_intel * winner["draw_prob"] + w_score * poisson_probs.get("draw", 0.33)
        away = w_intel * winner["away_win_prob"] + w_score * poisson_probs.get("away_win", 0.33)

        # v2: If blended draw exceeds 30%, dampen it
        if draw > 0.30:
            excess = draw - 0.30
            draw = 0.30
            # Redistribute excess to win probabilities proportionally
            total_wins = home + away
            if total_wins > 0:
                home += excess * (home / total_wins)
                away += excess * (away / total_wins)

        total = home + draw + away
        return {
            "home_win": round(home / total, 4),
            "draw": round(draw / total, 4),
            "away_win": round(away / total, 4),
        }

    @property
    def available_teams(self) -> list:
        """List all available teams."""
        return self._loader.list_teams()
