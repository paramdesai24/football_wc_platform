"""
Winner Prediction Engine — v2.0
=================================
Generates match outcome probabilities (home win / draw / away win)
using a weighted combination of Elo ratings, attack/defense matchups,
recent form, squad strength, and confederation intelligence.

v2 changes:
- Reduced draw probability ceiling (30% max vs 38%)
- Faster draw decay with Elo gap
- Tactical draw tendency integration
- Better normalization preventing draw inflation
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple

from ..utils.constants import (
    ELO_SCALE_FACTOR, ELO_HOME_BONUS, ELO_NEUTRAL_BONUS,
    BASE_DRAW_PROBABILITY, DRAW_ELO_SENSITIVITY,
    MAX_DRAW_PROBABILITY, MIN_DRAW_PROBABILITY,
    PREDICTION_WEIGHTS, HOME_ADVANTAGE_CONFIG,
    CONFEDERATION_STRENGTH, CONFEDERATION_UPSET_FACTOR,
    TOURNAMENT_IMPORTANCE,
    TACTICAL_PROFILES, DEFAULT_TACTICAL_PROFILE,
)
from ..utils.helpers import clamp

logger = logging.getLogger("match_engine.winner_prediction")


class WinnerPredictor:
    """
    Predicts match outcomes with explainable, football-realistic probabilities.

    Combines multiple intelligence signals:
    - Elo-based expected score
    - Attack/defense rating matchup
    - Recent form differential
    - Squad strength comparison
    - Confederation effects
    - Home advantage
    - Tournament importance
    - Tactical profiles (v2)
    """

    def __init__(self, league_averages: Dict[str, float]):
        self.averages = league_averages

    def predict(
        self,
        home_team: Dict[str, Any],
        away_team: Dict[str, Any],
        venue: str = "neutral",
        tournament: str = "friendly",
    ) -> Dict[str, Any]:
        """
        Predict match outcome probabilities.

        Returns dict with home_win_prob, draw_prob, away_win_prob,
        predicted_winner, margin, contributions
        """
        # 1. Compute individual signal probabilities
        elo_prob = self._elo_probability(home_team, away_team, venue)
        ad_prob = self._attack_defense_probability(home_team, away_team)
        form_prob = self._form_probability(home_team, away_team)
        squad_prob = self._squad_probability(home_team, away_team)
        conf_prob = self._confederation_probability(home_team, away_team)

        # 2. Weighted combination
        weights = PREDICTION_WEIGHTS
        raw_home = (
            weights["elo"] * elo_prob["home"]
            + weights["attack_defense"] * ad_prob["home"]
            + weights["form"] * form_prob["home"]
            + weights["squad"] * squad_prob["home"]
            + weights["confederation"] * conf_prob["home"]
        )
        raw_away = (
            weights["elo"] * elo_prob["away"]
            + weights["attack_defense"] * ad_prob["away"]
            + weights["form"] * form_prob["away"]
            + weights["squad"] * squad_prob["away"]
            + weights["confederation"] * conf_prob["away"]
        )

        # 3. Compute draw probability (higher when teams are close)
        draw_prob = self._compute_draw_probability(
            home_team, away_team, raw_home, raw_away
        )

        # 4. Apply home advantage boost
        venue_config = HOME_ADVANTAGE_CONFIG.get(venue, HOME_ADVANTAGE_CONFIG["neutral"])
        raw_home += venue_config["win_prob_boost"]

        # 5. Apply tournament importance effects
        tourn_mult = TOURNAMENT_IMPORTANCE.get(tournament, 1.0)
        # Higher-stakes matches slightly compress probabilities toward 50/50
        compression = 1.0 - (tourn_mult - 1.0) * 0.03
        compression = clamp(compression, 0.90, 1.0)

        # 6. Normalize to valid probabilities
        home_win, draw_final, away_win = self._normalize_probabilities(
            raw_home, draw_prob, raw_away, compression
        )

        # 7. Determine predicted winner
        predicted_winner, margin = self._determine_winner(
            home_team, away_team, home_win, draw_final, away_win
        )

        # 8. Build contributions breakdown
        contributions = {
            "elo": {
                "home": elo_prob["home"],
                "away": elo_prob["away"],
                "weight": weights["elo"],
            },
            "attack_defense": {
                "home": ad_prob["home"],
                "away": ad_prob["away"],
                "weight": weights["attack_defense"],
            },
            "form": {
                "home": form_prob["home"],
                "away": form_prob["away"],
                "weight": weights["form"],
            },
            "squad": {
                "home": squad_prob["home"],
                "away": squad_prob["away"],
                "weight": weights["squad"],
            },
            "confederation": {
                "home": conf_prob["home"],
                "away": conf_prob["away"],
                "weight": weights["confederation"],
            },
        }

        return {
            "home_team": home_team.get("country_name", "Home"),
            "away_team": away_team.get("country_name", "Away"),
            "home_win_prob": round(home_win, 4),
            "draw_prob": round(draw_final, 4),
            "away_win_prob": round(away_win, 4),
            "predicted_winner": predicted_winner,
            "margin": round(margin, 4),
            "venue": venue,
            "tournament": tournament,
            "contributions": contributions,
        }

    # ── Signal Probability Generators ─────────────────────────

    def _elo_probability(
        self, home: Dict, away: Dict, venue: str
    ) -> Dict[str, float]:
        """
        Elo-based win probability using the standard logistic model.
        P(home) = 1 / (1 + 10^((elo_away - elo_home + bonus) / 400))
        """
        elo_h = home.get("elo_rating", 1500)
        elo_a = away.get("elo_rating", 1500)

        # Venue bonus
        bonus = HOME_ADVANTAGE_CONFIG.get(venue, HOME_ADVANTAGE_CONFIG["neutral"])["elo_bonus"]

        elo_diff = elo_h + bonus - elo_a
        expected_home = 1.0 / (1.0 + 10.0 ** (-elo_diff / ELO_SCALE_FACTOR))
        expected_away = 1.0 - expected_home

        return {"home": expected_home, "away": expected_away}

    def _attack_defense_probability(self, home: Dict, away: Dict) -> Dict[str, float]:
        """
        Probability derived from attack vs defense matchup.
        Compares each team's attack against the opponent's defense.
        """
        avg_att = self.averages.get("attack_rating", 70.0)
        avg_def = self.averages.get("defense_rating", 70.0)

        home_att = home.get("attack_rating", avg_att)
        home_def = home.get("defense_rating", avg_def)
        away_att = away.get("attack_rating", avg_att)
        away_def = away.get("defense_rating", avg_def)

        # Strength indices: ratio of attack to opponent defense
        home_strength = (home_att / avg_att) * (avg_def / away_def) if away_def > 0 else 1.0
        away_strength = (away_att / avg_att) * (avg_def / home_def) if home_def > 0 else 1.0

        total = home_strength + away_strength
        if total == 0:
            return {"home": 0.5, "away": 0.5}

        return {
            "home": home_strength / total,
            "away": away_strength / total,
        }

    def _form_probability(self, home: Dict, away: Dict) -> Dict[str, float]:
        """Probability from recent form comparison."""
        avg_form = self.averages.get("recent_form_score", 0.5)

        h_form = home.get("recent_form_score", avg_form)
        a_form = away.get("recent_form_score", avg_form)

        h_momentum = home.get("momentum_score", 0.0)
        a_momentum = away.get("momentum_score", 0.0)

        h_adjusted = h_form + 0.05 * h_momentum
        a_adjusted = a_form + 0.05 * a_momentum

        h_adjusted = max(h_adjusted, 0.05)
        a_adjusted = max(a_adjusted, 0.05)

        total = h_adjusted + a_adjusted
        return {
            "home": h_adjusted / total,
            "away": a_adjusted / total,
        }

    def _squad_probability(self, home: Dict, away: Dict) -> Dict[str, float]:
        """Probability from squad overall strength comparison."""
        avg_sq = self.averages.get("squad_overall_strength", 0.5)

        h_sq = home.get("squad_overall_strength", avg_sq)
        a_sq = away.get("squad_overall_strength", avg_sq)

        h_conf = home.get("squad_confidence", 0.5)
        a_conf = away.get("squad_confidence", 0.5)

        h_adjusted = h_sq * (0.8 + 0.2 * h_conf)
        a_adjusted = a_sq * (0.8 + 0.2 * a_conf)

        h_adjusted = max(h_adjusted, 0.01)
        a_adjusted = max(a_adjusted, 0.01)

        total = h_adjusted + a_adjusted
        return {
            "home": h_adjusted / total,
            "away": a_adjusted / total,
        }

    def _confederation_probability(self, home: Dict, away: Dict) -> Dict[str, float]:
        """Subtle confederation-based probability adjustment."""
        h_conf_str = home.get("confederation_strength", 0.5)
        a_conf_str = away.get("confederation_strength", 0.5)

        h_density = 1.0 if home.get("data_density_tier") == "HIGH" else 0.7
        a_density = 1.0 if away.get("data_density_tier") == "HIGH" else 0.7

        h_score = h_density * 0.5 + (1 - h_density) * h_conf_str
        a_score = a_density * 0.5 + (1 - a_density) * a_conf_str

        h_score = max(h_score, 0.01)
        a_score = max(a_score, 0.01)

        total = h_score + a_score
        return {
            "home": h_score / total,
            "away": a_score / total,
        }

    # ── Draw and Normalization ────────────────────────────────

    def _compute_draw_probability(
        self, home: Dict, away: Dict, raw_home: float, raw_away: float
    ) -> float:
        """
        Compute draw probability based on team proximity.

        v2 changes:
        - Lower base (0.22 vs 0.25)
        - Faster Elo decay (sensitivity=400 vs 600)
        - Tactical draw tendency integration
        - Strength gap penalty for mismatched teams
        """
        # Elo proximity — closer Elo = higher draw chance
        elo_h = home.get("elo_rating", 1500)
        elo_a = away.get("elo_rating", 1500)
        elo_gap = abs(elo_h - elo_a)

        # Draw probability peaks when teams are equal, decays with Elo gap
        elo_draw = BASE_DRAW_PROBABILITY * np.exp(-elo_gap / DRAW_ELO_SENSITIVITY)

        # Probability proximity — if predicted probs are close, draw is more likely
        prob_gap = abs(raw_home - raw_away)
        prob_draw = BASE_DRAW_PROBABILITY * (1.0 - 2.0 * prob_gap)
        prob_draw = max(prob_draw, 0.0)

        # Combine with more weight on Elo gap
        draw = 0.65 * elo_draw + 0.35 * prob_draw

        # v2: Apply tactical draw tendency
        h_name = home.get("country_name", "")
        a_name = away.get("country_name", "")
        h_tactic = TACTICAL_PROFILES.get(h_name, DEFAULT_TACTICAL_PROFILE)
        a_tactic = TACTICAL_PROFILES.get(a_name, DEFAULT_TACTICAL_PROFILE)
        draw += (h_tactic["draw_tendency"] + a_tactic["draw_tendency"]) / 2.0

        # v2: Additional penalty for large strength gaps
        # Big mismatches should have lower draw probability
        if elo_gap > 200:
            draw *= 0.85
        elif elo_gap > 100:
            draw *= 0.92

        return clamp(draw, MIN_DRAW_PROBABILITY, MAX_DRAW_PROBABILITY)

    def _normalize_probabilities(
        self, raw_home: float, draw: float, raw_away: float, compression: float = 1.0
    ) -> Tuple[float, float, float]:
        """
        Normalize home/draw/away probabilities to sum to exactly 1.0.
        """
        # Apply compression toward 50/50
        if compression < 1.0:
            midpoint = 0.5
            raw_home = midpoint + compression * (raw_home - midpoint)
            raw_away = midpoint + compression * (raw_away - midpoint)

        # Allocate draw from the win probabilities
        home_win = raw_home * (1.0 - draw)
        away_win = raw_away * (1.0 - draw)

        # Ensure valid
        home_win = max(home_win, 0.01)
        away_win = max(away_win, 0.01)
        draw = max(draw, 0.01)

        # Normalize to 1.0
        total = home_win + draw + away_win
        home_win /= total
        draw /= total
        away_win /= total

        return home_win, draw, away_win

    def _determine_winner(
        self, home: Dict, away: Dict,
        home_win: float, draw: float, away_win: float
    ) -> Tuple[str, float]:
        """Determine the predicted winner and victory margin."""
        home_name = home.get("country_name", "Home")
        away_name = away.get("country_name", "Away")

        if home_win > away_win and home_win > draw:
            return home_name, home_win - max(draw, away_win)
        elif away_win > home_win and away_win > draw:
            return away_name, away_win - max(draw, home_win)
        else:
            return "Draw", draw - max(home_win, away_win)
