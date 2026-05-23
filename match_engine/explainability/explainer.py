"""
Prediction Explainability Engine
==================================
Generates human-readable, feature-attributed explanations for
every match prediction. Breaks down WHY a team is favored.
"""

import logging
from typing import Dict, Any, List

from ..utils.helpers import format_probability, elo_tier, rating_tier

logger = logging.getLogger("match_engine.explainability")


class PredictionExplainer:
    """
    Produces explainable prediction narratives.
    
    For every prediction, outputs:
    - Feature contribution percentages
    - Natural language explanation
    - Advantage breakdown by category
    """

    def explain(
        self,
        prediction: Dict[str, Any],
        home_team: Dict[str, Any],
        away_team: Dict[str, Any],
        confidence: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate full explanation for a prediction.

        Returns
        -------
        dict with narrative, advantages, factors, and summary
        """
        h_name = prediction.get("home_team", "Home")
        a_name = prediction.get("away_team", "Away")

        # 1. Build advantage breakdown
        advantages = self._compute_advantages(home_team, away_team)

        # 2. Contribution analysis from prediction
        contributions = prediction.get("contributions", {})
        factor_summary = self._summarize_contributions(contributions, h_name, a_name)

        # 3. Natural language narrative
        narrative = self._build_narrative(
            prediction, home_team, away_team, advantages, confidence
        )

        # 4. Key factors list
        key_factors = self._key_factors(prediction, advantages, h_name, a_name)

        return {
            "home_team": h_name,
            "away_team": a_name,
            "narrative": narrative,
            "key_factors": key_factors,
            "advantages": advantages,
            "factor_summary": factor_summary,
            "confidence_note": self._confidence_note(confidence),
        }

    def _compute_advantages(
        self, home: Dict, away: Dict
    ) -> Dict[str, Dict[str, Any]]:
        """Compute who has the advantage in each category."""
        categories = {
            "elo": {
                "home": home.get("elo_rating", 1500),
                "away": away.get("elo_rating", 1500),
                "label": "Elo Rating",
            },
            "attack": {
                "home": home.get("attack_rating", 50),
                "away": away.get("attack_rating", 50),
                "label": "Attack Rating",
            },
            "defense": {
                "home": home.get("defense_rating", 50),
                "away": away.get("defense_rating", 50),
                "label": "Defensive Strength",
            },
            "form": {
                "home": home.get("recent_form_score", 0.5),
                "away": away.get("recent_form_score", 0.5),
                "label": "Recent Form",
            },
            "squad": {
                "home": home.get("squad_overall_strength", 0.5),
                "away": away.get("squad_overall_strength", 0.5),
                "label": "Squad Quality",
            },
        }

        results = {}
        for key, data in categories.items():
            diff = data["home"] - data["away"]
            if abs(diff) < 0.01 * max(abs(data["home"]), abs(data["away"]), 1):
                winner = "Even"
            elif diff > 0:
                winner = home.get("country_name", "Home")
            else:
                winner = away.get("country_name", "Away")

            results[key] = {
                "label": data["label"],
                "home_value": round(data["home"], 2),
                "away_value": round(data["away"], 2),
                "difference": round(diff, 2),
                "advantage": winner,
            }

        return results

    def _summarize_contributions(
        self, contributions: Dict, h_name: str, a_name: str
    ) -> List[Dict[str, Any]]:
        """Summarize weighted factor contributions."""
        summary = []
        for factor, data in contributions.items():
            h_prob = data.get("home", 0.5)
            a_prob = data.get("away", 0.5)
            weight = data.get("weight", 0)
            favors = h_name if h_prob > a_prob else a_name if a_prob > h_prob else "Neither"
            summary.append({
                "factor": factor.replace("_", " ").title(),
                "weight": f"{weight * 100:.0f}%",
                "home_signal": round(h_prob, 3),
                "away_signal": round(a_prob, 3),
                "favors": favors,
            })
        return summary

    def _build_narrative(
        self, prediction: Dict, home: Dict, away: Dict,
        advantages: Dict, confidence: Dict
    ) -> str:
        """Build a natural language explanation."""
        h_name = prediction["home_team"]
        a_name = prediction["away_team"]
        winner = prediction["predicted_winner"]
        h_prob = prediction["home_win_prob"]
        a_prob = prediction["away_win_prob"]
        draw_p = prediction["draw_prob"]

        parts = []

        # Opening
        if winner == "Draw":
            parts.append(
                f"{h_name} vs {a_name} is predicted to be an evenly contested match "
                f"with a draw probability of {format_probability(draw_p)}."
            )
        else:
            margin = max(h_prob, a_prob) - min(h_prob, a_prob)
            if margin > 0.30:
                strength = "strongly"
            elif margin > 0.15:
                strength = "comfortably"
            else:
                strength = "narrowly"
            win_prob = h_prob if winner == h_name else a_prob
            parts.append(
                f"{winner} is {strength} favored with a {format_probability(win_prob)} "
                f"win probability against {a_name if winner == h_name else h_name}."
            )

        # Advantages
        adv_parts = []
        for key, adv in advantages.items():
            if adv["advantage"] != "Even":
                adv_parts.append(f"{adv['label'].lower()} ({adv['advantage']})")

        if adv_parts:
            parts.append(f"Key advantages: {', '.join(adv_parts[:3])}.")

        # Scoreline
        parts.append(
            f"Expected scoreline: {prediction.get('predicted_score', 'N/A')} "
            f"(xG: {prediction.get('home_xg', '?')}-{prediction.get('away_xg', '?')})."
        )

        # Confidence
        conf_tier = confidence.get("confidence_tier", "medium")
        conf_score = confidence.get("confidence_score", 0.5)
        parts.append(f"Prediction confidence: {conf_tier} ({format_probability(conf_score)}).")

        return " ".join(parts)

    def _key_factors(
        self, prediction: Dict, advantages: Dict, h_name: str, a_name: str
    ) -> List[str]:
        """Extract top key factors for the prediction."""
        factors = []
        winner = prediction["predicted_winner"]

        for key, adv in advantages.items():
            if adv["advantage"] == winner and adv["advantage"] != "Even":
                diff = abs(adv["difference"])
                if key == "elo" and diff > 50:
                    factors.append(f"Superior Elo rating ({adv['home_value']} vs {adv['away_value']})")
                elif key == "attack" and diff > 5:
                    factors.append(f"Stronger attack ({adv['home_value']} vs {adv['away_value']})")
                elif key == "defense" and diff > 5:
                    factors.append(f"Better defensive record ({adv['home_value']} vs {adv['away_value']})")
                elif key == "form" and diff > 0.05:
                    factors.append(f"Better recent form ({adv['home_value']:.3f} vs {adv['away_value']:.3f})")
                elif key == "squad" and diff > 0.03:
                    factors.append(f"Higher squad quality ({adv['home_value']:.3f} vs {adv['away_value']:.3f})")

        if not factors:
            factors.append("Closely matched teams with marginal differences")

        return factors[:5]

    def _confidence_note(self, confidence: Dict) -> str:
        """Generate a confidence context note."""
        tier = confidence.get("confidence_tier", "medium")
        if tier in ("very_high", "high"):
            return "High data availability for both teams — prediction is well-supported."
        elif tier == "medium":
            return "Moderate data coverage — prediction has reasonable support."
        else:
            return "Limited data for one or both teams — prediction carries higher uncertainty."
