"""
Prediction Confidence Engine
==============================
Scores the confidence of each prediction based on data quality,
feature completeness, team data density, and historical reliability.
"""

import logging
from typing import Dict, Any

from ..utils.constants import CONFIDENCE_THRESHOLDS
from ..utils.helpers import clamp

logger = logging.getLogger("match_engine.confidence")


class ConfidenceEngine:
    """
    Generates a prediction confidence score (0.0 – 1.0) for each match.
    
    Factors:
    - Data density tier (HIGH/MEDIUM/LOW) for both teams
    - Feature completeness (are all signals available?)
    - Historical sample size
    - Squad intelligence quality
    - Form data coverage
    - Elo rating reliability
    """

    def score(
        self,
        home_team: Dict[str, Any],
        away_team: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Compute prediction confidence for a matchup.

        Returns
        -------
        dict with confidence_score, confidence_tier, and breakdown
        """
        h_scores = self._team_confidence(home_team)
        a_scores = self._team_confidence(away_team)

        # Overall = average of both teams' confidence
        overall = 0.5 * h_scores["total"] + 0.5 * a_scores["total"]
        overall = clamp(overall, 0.0, 1.0)

        tier = self._classify_tier(overall)

        return {
            "confidence_score": round(overall, 4),
            "confidence_tier": tier,
            "home_confidence": h_scores,
            "away_confidence": a_scores,
        }

    def _team_confidence(self, team: Dict[str, Any]) -> Dict[str, float]:
        """Compute confidence components for a single team."""
        scores = {}

        # 1. Data density tier
        tier = team.get("data_density_tier", "LOW")
        tier_map = {"HIGH": 1.0, "MEDIUM": 0.65, "LOW": 0.30}
        scores["data_density"] = tier_map.get(tier, 0.30)

        # 2. Feature completeness
        required = ["elo_rating", "attack_rating", "defense_rating",
                     "recent_form_score", "squad_overall_strength"]
        available = sum(1 for f in required if team.get(f) is not None)
        scores["feature_completeness"] = available / len(required)

        # 3. Sample size (more matches = more reliable)
        sample = team.get("sample_size", 0)
        if sample >= 100:
            scores["sample_reliability"] = 1.0
        elif sample >= 50:
            scores["sample_reliability"] = 0.80
        elif sample >= 20:
            scores["sample_reliability"] = 0.60
        else:
            scores["sample_reliability"] = 0.35

        # 4. Squad intelligence quality
        sq_conf = team.get("squad_confidence", 0.5)
        scores["squad_quality"] = clamp(sq_conf, 0.0, 1.0)

        # 5. Elo reliability (not a fallback)
        if team.get("missing_elo", False) or team.get("fallback_used", False):
            scores["elo_reliability"] = 0.40
        else:
            scores["elo_reliability"] = 1.0

        # 6. Confidence adjustment from Phase 2
        conf_adj = team.get("confidence_adjustment", 0.5)
        scores["phase2_confidence"] = clamp(conf_adj, 0.0, 1.0)

        # Weighted total
        weights = {
            "data_density": 0.25,
            "feature_completeness": 0.20,
            "sample_reliability": 0.20,
            "squad_quality": 0.10,
            "elo_reliability": 0.15,
            "phase2_confidence": 0.10,
        }
        total = sum(weights[k] * scores[k] for k in weights)
        scores["total"] = round(clamp(total, 0.0, 1.0), 4)

        return scores

    def _classify_tier(self, score: float) -> str:
        """Classify confidence into a human-readable tier."""
        for tier, threshold in sorted(
            CONFIDENCE_THRESHOLDS.items(),
            key=lambda x: x[1],
            reverse=True,
        ):
            if score >= threshold:
                return tier
        return "very_low"
