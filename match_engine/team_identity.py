"""
Team Identity Persistence Engine
==================================
Derives and enriches team identity metrics to reduce match independence
and improve prediction consistency based on team quality.

Metrics:
- offensive_rating: Combined attack quality (attack_rating + squad_attack_score)
- defensive_rating: Combined defense quality (defense_rating + squad_defense_score)
- form_modifier: Recent momentum with consistency dampening
- fatigue_factor: Accumulated fatigue from tournament matches
- consistency_factor: How consistent the team is (derived from recent_form_variance)
"""

import logging
from typing import Dict, Any, List
import numpy as np

logger = logging.getLogger("match_engine.team_identity")


class TeamIdentityEngine:
    """
    Enriches team data with identity persistence metrics
    that improve prediction consistency and reduce volatility.
    """

    def __init__(self):
        self._fatigue_cache: Dict[str, float] = {}
        self._match_history: Dict[str, List[float]] = {}

    def enrich_team_data(self, team_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add identity persistence metrics to a team's data dictionary.
        
        Returns an enriched copy with new fields:
        - offensive_rating (0-100)
        - defensive_rating (0-100)
        - form_modifier (0.5-1.5)
        - consistency_factor (0-1)
        """
        enriched = team_data.copy()

        # ── OFFENSIVE RATING ──
        # Combines attack_rating (strength) with squad_attack_score (quality)
        attack_rating = enriched.get("attack_rating", 75.0)
        squad_attack = enriched.get("squad_attack_score", 0.5)
        
        # Normalize squad_attack from (0-1) to (0-1) relative to team's baseline
        squad_attack_adjusted = 0.5 + (squad_attack - 0.5) * 0.3
        offensive_rating = 0.7 * attack_rating + 0.3 * (squad_attack_adjusted * 100)
        enriched["offensive_rating"] = round(min(100, max(0, offensive_rating)), 1)

        # ── DEFENSIVE RATING ──
        # Combines defense_rating (strength) with squad_defense_score (quality)
        defense_rating = enriched.get("defense_rating", 83.0)
        squad_defense = enriched.get("squad_defense_score", 0.5)
        
        # Normalize squad_defense from (0-1) to (0-1) relative to team's baseline
        squad_defense_adjusted = 0.5 + (squad_defense - 0.5) * 0.3
        defensive_rating = 0.7 * defense_rating + 0.3 * (squad_defense_adjusted * 100)
        enriched["defensive_rating"] = round(min(100, max(0, defensive_rating)), 1)

        # ── FORM MODIFIER ──
        # Combines recent form with consistency dampening
        recent_form = enriched.get("recent_form_score", 0.5)
        momentum = enriched.get("momentum_score", 0.0)
        consistency = enriched.get("consistency_score", 0.5)
        
        # Form modifier: base recent form boosted by momentum, tempered by consistency
        # Consistency acts as a variance dampener (high consistency = momentum matters more)
        form_modifier = (
            0.5 +
            0.4 * (recent_form - 0.5) +  # Recent form effect
            0.15 * momentum * (0.5 + consistency)  # Momentum, dampened by consistency
        )
        form_modifier = max(0.5, min(1.5, form_modifier))  # Clamp to (0.5, 1.5)
        enriched["form_modifier"] = round(form_modifier, 3)

        # ── CONSISTENCY FACTOR ──
        # How stable/predictable the team is (0=erratic, 1=very consistent)
        consistency_factor = enriched.get("consistency_score", 0.5)
        enriched["consistency_factor"] = round(consistency_factor, 3)

        # ── FATIGUE FACTOR ──
        # Initialized to 1.0, updated by tournament simulator
        if "fatigue_factor" not in enriched:
            enriched["fatigue_factor"] = 1.0

        # ── SQUAD DEPTH FACTOR ──
        # Influences resilience through fatigue accumulation
        squad_depth = enriched.get("squad_depth_score", 0.5)
        enriched["squad_depth_factor"] = round(0.5 + squad_depth * 0.5, 3)

        return enriched

    def record_match_result(self, team_name: str, goals_scored: int, goals_conceded: int):
        """
        Record a match result for fatigue tracking.
        
        Used by tournament simulator to track fatigue from multiple matches.
        """
        if team_name not in self._match_history:
            self._match_history[team_name] = []
        
        self._match_history[team_name].append(goals_scored - goals_conceded)

    def update_fatigue(self, team_name: str, matches_in_tournament: int,
                      days_rest: int, squad_depth_factor: float = 0.75) -> float:
        """
        Calculate fatigue factor based on matches played and rest.
        
        Args:
            team_name: Team identifier
            matches_in_tournament: Number of matches played so far
            days_rest: Days since last match
            squad_depth_factor: How well the team handles fatigue (0.5-1.0)
        
        Returns:
            fatigue_factor (0.85-1.0), where lower = more fatigued
        """
        # Base fatigue from match accumulation (World Cup max is 7 matches)
        # Each match costs ~1.5% performance, but squad depth helps
        fatigue_from_matches = 1.0 - (matches_in_tournament * 0.015 * (2.0 - squad_depth_factor))
        
        # Recovery from rest
        # Full recovery takes ~3 days; each day provides ~10% recovery
        recovery_rate = min(1.0, days_rest * 0.10)
        
        # Combine: fatigue reduced by recovery, but not below 0.85 (even 7 matches + no rest)
        fatigue_factor = max(0.85, fatigue_from_matches + recovery_rate * 0.15)
        
        self._fatigue_cache[team_name] = round(fatigue_factor, 3)
        return fatigue_factor

    def get_fatigue_factor(self, team_name: str) -> float:
        """Get cached fatigue factor or return default 1.0."""
        return self._fatigue_cache.get(team_name, 1.0)

    def reset_tournament(self):
        """Clear fatigue and match history for new tournament."""
        self._fatigue_cache.clear()
        self._match_history.clear()
