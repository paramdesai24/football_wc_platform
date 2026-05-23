"""
Expected Goals (xG) Engine — v2.0
====================================
Generates expected goals using NONLINEAR attack/defense interaction,
tactical profiles, and properly amplified team separation.

Key changes from v1:
- Nonlinear power scaling for attack and defense factors
- Attack×Defense interaction amplifier for mismatches
- Tactical profile modifiers per team
- Wider xG separation (realistic 0.4–3.5 range)
- Proper Elo influence on xG
"""

import logging
import numpy as np
from typing import Dict, Any

from ..utils.constants import (
    BASE_GOALS_PER_TEAM, MAX_REALISTIC_XG, MIN_REALISTIC_XG,
    HOME_ADVANTAGE_CONFIG,
    TOURNAMENT_SCORING_MODIFIER,
    ATTACK_RATING_MEAN, DEFENSE_RATING_MEAN,
    ATTACK_RATING_MAX, ATTACK_RATING_MIN,
    DEFENSE_RATING_MAX, DEFENSE_RATING_MIN,
    XG_ATTACK_POWER, XG_DEFENSE_POWER,
    XG_ELO_DIVISOR, XG_ELO_CLAMP,
    XG_FORM_SENSITIVITY, XG_SQUAD_SENSITIVITY,
    TACTICAL_PROFILES, DEFAULT_TACTICAL_PROFILE,
)
from ..utils.helpers import clamp, safe_divide

logger = logging.getLogger("match_engine.expected_goals")


class ExpectedGoalsEngine:
    """
    Computes expected goals (xG) for each team in a match.

    v2 uses a MULTIPLICATIVE model with nonlinear scaling:
        xG = base_rate × attack_factor^p × defense_factor^p × elo × form × squad × home × tactical × tournament
    """

    def __init__(self, league_averages: Dict[str, float]):
        self.averages = league_averages

    def compute(
        self,
        home_team: Dict[str, Any],
        away_team: Dict[str, Any],
        venue: str = "neutral",
        tournament: str = "friendly",
    ) -> Dict[str, Any]:
        """Compute expected goals for both teams."""
        home_factors = self._compute_factors(home_team, away_team, True, venue)
        home_xg = self._calculate_xg(home_factors, tournament)

        away_factors = self._compute_factors(away_team, home_team, False, venue)
        away_xg = self._calculate_xg(away_factors, tournament)

        # Apply tactical profiles (halved impact — base factors already do heavy lifting)
        h_name = home_team.get("country_name", "")
        a_name = away_team.get("country_name", "")
        h_tactic = TACTICAL_PROFILES.get(h_name, DEFAULT_TACTICAL_PROFILE)
        a_tactic = TACTICAL_PROFILES.get(a_name, DEFAULT_TACTICAL_PROFILE)

        # Tactical modifiers: blend toward 1.0 to halve their impact
        h_att_mod = 1.0 + (h_tactic["attack_mod"] - 1.0) * 0.5
        a_att_mod = 1.0 + (a_tactic["attack_mod"] - 1.0) * 0.5
        h_def_mod = 1.0 + (h_tactic["defense_mod"] - 1.0) * 0.5
        a_def_mod = 1.0 + (a_tactic["defense_mod"] - 1.0) * 0.5

        home_xg *= h_att_mod * a_def_mod
        away_xg *= a_att_mod * h_def_mod

        # Total xG realism check: international matches average ~2.7 total goals
        # If total exceeds 3.5, scale both back with soft cap (higher blend = more conservative)
        total_xg = home_xg + away_xg
        if total_xg > 3.5:
            scale = 3.5 / total_xg
            # Blend: apply more aggressive scaling (0.85 vs 0.75) to reduce extreme volatility
            scale = 1.0 + (scale - 1.0) * 0.85
            home_xg *= scale
            away_xg *= scale

        # Clamp to realistic bounds
        home_xg = clamp(home_xg, MIN_REALISTIC_XG, MAX_REALISTIC_XG)
        away_xg = clamp(away_xg, MIN_REALISTIC_XG, MAX_REALISTIC_XG)

        return {
            "home_xg": round(home_xg, 2),
            "away_xg": round(away_xg, 2),
            "total_xg": round(home_xg + away_xg, 2),
            "home_factors": home_factors,
            "away_factors": away_factors,
            "home_tactical": h_tactic,
            "away_tactical": a_tactic,
        }

    def _compute_factors(
        self, attacking: Dict, defending: Dict, is_home: bool, venue: str
    ) -> Dict[str, float]:
        """Compute multiplicative factors for xG calculation with nonlinear scaling."""
        avg_att = self.averages.get("attack_rating", ATTACK_RATING_MEAN)
        avg_def = self.averages.get("defense_rating", DEFENSE_RATING_MEAN)
        avg_elo = self.averages.get("elo_rating", 1500)
        avg_form = self.averages.get("recent_form_score", 0.5)
        avg_sq = self.averages.get("squad_overall_strength", 0.5)

        # ── ATTACK FACTOR (nonlinear) ──
        # Normalize attack rating to 0-1 scale, then apply power scaling
        att_rating = attacking.get("attack_rating", avg_att)
        att_normalized = (att_rating - ATTACK_RATING_MIN) / (ATTACK_RATING_MAX - ATTACK_RATING_MIN)
        att_normalized = clamp(att_normalized, 0.0, 1.0)
        # Map to xG multiplier: 0.70 (worst) to 1.35 (best), with power curve
        attack_factor = 0.70 + 0.65 * (att_normalized ** XG_ATTACK_POWER)

        # ── DEFENSE FACTOR (nonlinear — opponent's defense suppresses goals) ──
        def_rating = defending.get("defense_rating", avg_def)
        def_normalized = (def_rating - DEFENSE_RATING_MIN) / (DEFENSE_RATING_MAX - DEFENSE_RATING_MIN)
        def_normalized = clamp(def_normalized, 0.0, 1.0)
        # Invert: strong defense = lower factor. Map to 0.65 (best defense) to 1.30 (worst defense)
        defense_factor = 1.30 - 0.65 * (def_normalized ** XG_DEFENSE_POWER)

        # ── ATTACK×DEFENSE INTERACTION AMPLIFIER ──
        # When a strong attack faces a weak defense, amplify the effect
        interaction = attack_factor * defense_factor
        # If interaction > 1.0, it's a mismatch favoring the attacker — amplify slightly
        if interaction > 1.05:
            interaction = 1.0 + (interaction - 1.0) * 1.15
        elif interaction < 0.95:
            interaction = 1.0 + (interaction - 1.0) * 1.10

        # ── ELO FACTOR ──
        att_elo = attacking.get("elo_rating", avg_elo)
        def_elo = defending.get("elo_rating", avg_elo)
        elo_diff = att_elo - def_elo
        elo_factor = 1.0 + elo_diff / XG_ELO_DIVISOR
        elo_factor = clamp(elo_factor, XG_ELO_CLAMP[0], XG_ELO_CLAMP[1])

        # ── FORM FACTOR ──
        att_form = attacking.get("recent_form_score", avg_form)
        form_ratio = safe_divide(att_form, avg_form, 1.0)
        form_factor = 1.0 + XG_FORM_SENSITIVITY * (form_ratio - 1.0)
        form_factor = clamp(form_factor, 0.70, 1.35)

        # ── SQUAD FACTOR ──
        att_sq = attacking.get("squad_overall_strength", avg_sq)
        squad_ratio = safe_divide(att_sq, avg_sq, 1.0)
        squad_factor = 1.0 + XG_SQUAD_SENSITIVITY * (squad_ratio - 1.0)
        squad_factor = clamp(squad_factor, 0.70, 1.35)

        # ── HOME ADVANTAGE ──
        venue_cfg = HOME_ADVANTAGE_CONFIG.get(venue, HOME_ADVANTAGE_CONFIG["neutral"])
        home_factor = 1.0
        if is_home:
            home_factor = 1.0 + venue_cfg["goal_boost"] / BASE_GOALS_PER_TEAM

        return {
            "attack_factor": round(attack_factor, 4),
            "defense_factor": round(defense_factor, 4),
            "interaction": round(interaction, 4),
            "elo_factor": round(elo_factor, 4),
            "form_factor": round(form_factor, 4),
            "squad_factor": round(squad_factor, 4),
            "home_factor": round(home_factor, 4),
            "base_rate": BASE_GOALS_PER_TEAM,
        }

    def _calculate_xg(self, factors: Dict[str, float], tournament: str) -> float:
        """
        Calculate expected goals using pure multiplicative model.
        xG = base × interaction × elo × form × squad × home × tournament
        """
        tourn_mod = TOURNAMENT_SCORING_MODIFIER.get(tournament, 1.0)

        xg = (
            factors["base_rate"]
            * factors["interaction"]
            * factors["elo_factor"]
            * factors["form_factor"]
            * factors["squad_factor"]
            * factors["home_factor"]
            * tourn_mod
        )
        return xg
