"""
Team state helpers for tournament simulations.

These utilities keep offensive/defensive identity, form, fatigue,
and consistency persistent across a full tournament simulation.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping

from match_engine.utils.helpers import clamp


TEAM_STATE_BOUNDS = {
    "offensive_rating": (0.84, 1.16),
    "defensive_rating": (0.84, 1.16),
    "form_modifier": (0.84, 1.18),
    "fatigue": (0.0, 0.42),
    "consistency_factor": (0.84, 1.14),
    "morale": (0.82, 1.18),
    "confidence": (0.82, 1.18),
    "chemistry": (0.84, 1.15),
    "pressure_resilience": (0.82, 1.16),
    "tactical_intensity": (0.84, 1.16),
    "defensive_compactness": (0.84, 1.16),
    "recovery_rate": (0.84, 1.12),
    "momentum": (0.82, 1.22),
    "tournament_consistency": (0.84, 1.16),
    "pressure_handling": (0.82, 1.18),
}

STAGE_FATIGUE = {
    "group": 0.03,
    "GS": 0.03,
    "R32": 0.05,
    "R16": 0.07,
    "QF": 0.09,
    "SF": 0.11,
    "3rd_place": 0.10,
    "Final": 0.12,
}

SOFT_GOAL_CAP = {
    "group": 5,
    "GS": 5,
    "R32": 5,
    "R16": 5,
    "QF": 4,
    "SF": 3,
    "3rd_place": 4,
    "Final": 3,
}

AVERAGE_GOAL_CAP = 4


def build_team_state(team: Mapping[str, Any], league_averages: Mapping[str, Any]) -> Dict[str, float]:
    """Build the initial persistent state for a team."""
    avg_attack = float(league_averages.get("attack_rating", 75.0)) or 75.0
    avg_defense = float(league_averages.get("defense_rating", 75.0)) or 75.0
    avg_form = float(league_averages.get("recent_form_score", 0.5)) or 0.5
    avg_consistency = 0.5

    attack_rating = float(team.get("attack_rating", avg_attack))
    defense_rating = float(team.get("defense_rating", avg_defense))
    recent_form = float(team.get("recent_form_score", avg_form))
    momentum = float(team.get("momentum_score", 0.0))
    consistency = float(team.get("consistency_score", avg_consistency))

    offensive_rating = clamp(0.96 + (attack_rating - avg_attack) / 220.0, *TEAM_STATE_BOUNDS["offensive_rating"])
    defensive_rating = clamp(0.96 + (defense_rating - avg_defense) / 220.0, *TEAM_STATE_BOUNDS["defensive_rating"])
    form_modifier = clamp(0.96 + (recent_form - avg_form) * 0.55 + momentum * 0.03, *TEAM_STATE_BOUNDS["form_modifier"])
    consistency_factor = clamp(0.94 + (consistency - avg_consistency) * 0.40, *TEAM_STATE_BOUNDS["consistency_factor"])
    morale = clamp(0.96 + (recent_form - avg_form) * 0.40 + momentum * 0.02, *TEAM_STATE_BOUNDS["morale"])
    confidence = clamp(0.95 + (float(team.get("squad_confidence", 0.5)) - 0.5) * 0.25, *TEAM_STATE_BOUNDS["confidence"])
    chemistry = clamp(0.96 + float(team.get("squad_depth_score", 0.5)) * 0.05, *TEAM_STATE_BOUNDS["chemistry"])
    pressure_resilience = clamp(0.95 + consistency * 0.06, *TEAM_STATE_BOUNDS["pressure_resilience"])
    tactical_intensity = clamp(0.95 + (attack_rating - avg_attack) / 180.0, *TEAM_STATE_BOUNDS["tactical_intensity"])
    defensive_compactness = clamp(0.95 + (defense_rating - avg_defense) / 180.0, *TEAM_STATE_BOUNDS["defensive_compactness"])
    recovery_rate = clamp(0.95 + float(team.get("squad_depth_score", 0.5)) * 0.05, *TEAM_STATE_BOUNDS["recovery_rate"])

    return {
        "team_name": str(team.get("country_name", "")),
        "offensive_rating": offensive_rating,
        "defensive_rating": defensive_rating,
        "form_modifier": form_modifier,
        "fatigue": 0.0,
        "consistency_factor": consistency_factor,
        "tournament_consistency": consistency_factor,
        "momentum": clamp(0.98 + momentum * 0.02, *TEAM_STATE_BOUNDS["momentum"]),
        "morale": morale,
        "confidence": confidence,
        "chemistry": chemistry,
        "pressure_resilience": pressure_resilience,
        "pressure_handling": pressure_resilience,
        "tactical_intensity": tactical_intensity,
        "defensive_compactness": defensive_compactness,
        "recovery_rate": recovery_rate,
        "matches_played": 0.0,
        "goals_for": 0.0,
        "goals_against": 0.0,
    }


def apply_team_state(team: Mapping[str, Any], state: Mapping[str, Any] | None) -> Dict[str, Any]:
    """Overlay persistent state onto a team record before prediction."""
    adjusted = dict(team)
    if not state:
        return adjusted

    offense = clamp(float(state.get("offensive_rating", 1.0)), *TEAM_STATE_BOUNDS["offensive_rating"])
    defense = clamp(float(state.get("defensive_rating", 1.0)), *TEAM_STATE_BOUNDS["defensive_rating"])
    form = clamp(float(state.get("form_modifier", 1.0)), *TEAM_STATE_BOUNDS["form_modifier"])
    fatigue = clamp(float(state.get("fatigue", 0.0)), *TEAM_STATE_BOUNDS["fatigue"])
    consistency = clamp(float(state.get("consistency_factor", 1.0)), *TEAM_STATE_BOUNDS["consistency_factor"])
    tournament_consistency = clamp(float(state.get("tournament_consistency", consistency)), *TEAM_STATE_BOUNDS["tournament_consistency"])
    morale = clamp(float(state.get("morale", 1.0)), *TEAM_STATE_BOUNDS["morale"])
    confidence = clamp(float(state.get("confidence", 1.0)), *TEAM_STATE_BOUNDS["confidence"])
    momentum = clamp(float(state.get("momentum", 1.0)), *TEAM_STATE_BOUNDS["momentum"])
    chemistry = clamp(float(state.get("chemistry", 1.0)), *TEAM_STATE_BOUNDS["chemistry"])
    pressure_resilience = clamp(float(state.get("pressure_resilience", 1.0)), *TEAM_STATE_BOUNDS["pressure_resilience"])
    pressure_handling = clamp(float(state.get("pressure_handling", pressure_resilience)), *TEAM_STATE_BOUNDS["pressure_handling"])
    tactical_intensity = clamp(float(state.get("tactical_intensity", 1.0)), *TEAM_STATE_BOUNDS["tactical_intensity"])
    defensive_compactness = clamp(float(state.get("defensive_compactness", 1.0)), *TEAM_STATE_BOUNDS["defensive_compactness"])
    recovery_rate = clamp(float(state.get("recovery_rate", 1.0)), *TEAM_STATE_BOUNDS["recovery_rate"])

    base_attack = float(adjusted.get("attack_rating", 75.0))
    base_defense = float(adjusted.get("defense_rating", 75.0))
    base_form = float(adjusted.get("recent_form_score", 0.5))
    base_momentum = float(adjusted.get("momentum_score", 0.0))
    base_consistency = float(adjusted.get("consistency_score", 0.5))
    base_squad_confidence = float(adjusted.get("squad_confidence", 0.5))

    adjusted["attack_rating"] = round(base_attack * offense * tactical_intensity * morale * confidence * chemistry * momentum * (1.0 - fatigue * 0.10), 4)
    adjusted["defense_rating"] = round(base_defense * defense * defensive_compactness * pressure_resilience * pressure_handling * (1.0 - fatigue * 0.07), 4)
    adjusted["recent_form_score"] = round(clamp(base_form * form * morale, 0.10, 0.99), 4)
    adjusted["momentum_score"] = round(base_momentum + (momentum - 1.0) * 3.0 + (form - 1.0) * 2.0 + (morale - 1.0) * 1.5 - fatigue * 1.2, 4)
    adjusted["consistency_score"] = round(clamp(base_consistency * consistency * tournament_consistency * chemistry, 0.10, 0.99), 4)
    adjusted["squad_confidence"] = round(clamp(base_squad_confidence * confidence * morale * recovery_rate, 0.10, 0.99), 4)
    adjusted["fatigue_score"] = round(fatigue, 4)
    adjusted["morale"] = round(morale, 4)
    adjusted["confidence"] = round(confidence, 4)
    adjusted["chemistry"] = round(chemistry, 4)
    adjusted["pressure_resilience"] = round(pressure_resilience, 4)
    adjusted["pressure_handling"] = round(pressure_handling, 4)
    adjusted["tactical_intensity"] = round(tactical_intensity, 4)
    adjusted["defensive_compactness"] = round(defensive_compactness, 4)
    adjusted["recovery_rate"] = round(recovery_rate, 4)

    return adjusted


def soft_cap_goals(goals: int, stage: str) -> int:
    """Apply a soft ceiling that compresses extreme scorelines instead of hard-clipping them."""
    cap = SOFT_GOAL_CAP.get(stage, AVERAGE_GOAL_CAP)
    if goals <= cap:
        return goals
    overflow = goals - cap
    softened = cap + int(round(overflow * 0.35))
    return min(softened, cap + 1)


def update_team_state(
    state: Dict[str, Any] | None,
    goals_for: int,
    goals_against: int,
    stage: str,
    *,
    extra_time: bool = False,
    penalties: bool = False,
    upset: bool = False,
) -> Dict[str, Any] | None:
    """Update persistent team identity after a match."""
    if state is None:
        return None

    goal_diff = goals_for - goals_against
    stage_pressure = {
        "group": 0.00,
        "GS": 0.00,
        "R32": 0.015,
        "R16": 0.025,
        "QF": 0.035,
        "SF": 0.045,
        "3rd_place": 0.030,
        "Final": 0.055,
    }.get(stage, 0.01)
    stage_fatigue = STAGE_FATIGUE.get(stage, 0.03)
    state["matches_played"] = float(state.get("matches_played", 0)) + 1
    state["goals_for"] = float(state.get("goals_for", 0)) + goals_for
    state["goals_against"] = float(state.get("goals_against", 0)) + goals_against

    offense_delta = 0.010 * (goals_for - 1.1) + 0.006 * max(goal_diff, 0) - 0.004 * max(-goal_diff, 0)
    defense_delta = 0.010 * (1.1 - goals_against) + 0.006 * max(-goal_diff, 0) - 0.004 * max(goal_diff, 0)
    form_delta = 0.028 * (1 if goal_diff > 0 else -1 if goal_diff < 0 else 0) + 0.004 * goal_diff
    consistency_delta = 0.005 if abs(goal_diff) <= 1 else -0.005
    morale_delta = 0.018 * (1 if goal_diff > 0 else -1 if goal_diff < 0 else 0)
    confidence_delta = 0.014 * (1 if goal_diff > 0 else -1 if goal_diff < 0 else 0)
    chemistry_delta = 0.004 if abs(goal_diff) <= 1 else -0.003
    pressure_delta = -0.005 if goal_diff > 1 else 0.004 if goal_diff < 0 else 0.0
    tactical_delta = 0.004 * (1 if goals_for > goals_against else -1 if goals_for < goals_against else 0)
    compactness_delta = 0.004 * (1 if goals_against <= 1 else -1 if goals_against >= 3 else 0)
    recovery_delta = 0.003 if stage in {"group", "GS"} else -0.002
    momentum_delta = 0.020 * (1 if goal_diff > 0 else -1 if goal_diff < 0 else 0) + 0.004 * goal_diff

    if extra_time:
        stage_fatigue += 0.02
        form_delta -= 0.005
        morale_delta -= 0.008
        confidence_delta -= 0.006
    if penalties:
        stage_fatigue += 0.015
        consistency_delta -= 0.005
        morale_delta -= 0.004
        confidence_delta -= 0.004
    if upset:
        form_delta += 0.010
        morale_delta += 0.007
        confidence_delta += 0.005
        momentum_delta += 0.006

    pressure_handling = clamp(float(state.get("pressure_handling", state.get("pressure_resilience", 1.0))), *TEAM_STATE_BOUNDS["pressure_handling"])
    pressure_impact = stage_pressure * (1.0 - pressure_handling)

    tactical_load = max(0.0, float(state.get("tactical_intensity", 1.0)) - 1.0) * 0.012
    fatigue = clamp(
        float(state.get("fatigue", 0.0)) + stage_fatigue + tactical_load + stage_pressure * 0.35 + 0.010 * max(goals_for + goals_against - 2, 0),
        *TEAM_STATE_BOUNDS["fatigue"],
    )

    state["offensive_rating"] = clamp(float(state.get("offensive_rating", 1.0)) + offense_delta, *TEAM_STATE_BOUNDS["offensive_rating"])
    state["defensive_rating"] = clamp(float(state.get("defensive_rating", 1.0)) + defense_delta, *TEAM_STATE_BOUNDS["defensive_rating"])
    state["form_modifier"] = clamp(float(state.get("form_modifier", 1.0)) + form_delta - fatigue * 0.02, *TEAM_STATE_BOUNDS["form_modifier"])
    state["consistency_factor"] = clamp(float(state.get("consistency_factor", 1.0)) + consistency_delta - fatigue * 0.01 - pressure_impact * 0.20, *TEAM_STATE_BOUNDS["consistency_factor"])
    state["tournament_consistency"] = clamp(float(state.get("tournament_consistency", state.get("consistency_factor", 1.0))) + consistency_delta - pressure_impact * 0.25, *TEAM_STATE_BOUNDS["tournament_consistency"])
    state["fatigue"] = fatigue
    state["morale"] = clamp(float(state.get("morale", 1.0)) + morale_delta - fatigue * 0.01 - pressure_impact * 0.15, *TEAM_STATE_BOUNDS["morale"])
    state["confidence"] = clamp(float(state.get("confidence", 1.0)) + confidence_delta - fatigue * 0.008 - pressure_impact * 0.16, *TEAM_STATE_BOUNDS["confidence"])
    state["momentum"] = clamp(float(state.get("momentum", 1.0)) + momentum_delta - fatigue * 0.010, *TEAM_STATE_BOUNDS["momentum"])
    state["chemistry"] = clamp(float(state.get("chemistry", 1.0)) + chemistry_delta, *TEAM_STATE_BOUNDS["chemistry"])
    state["pressure_resilience"] = clamp(float(state.get("pressure_resilience", 1.0)) + pressure_delta - fatigue * 0.008 + stage_pressure * 0.10, *TEAM_STATE_BOUNDS["pressure_resilience"])
    state["pressure_handling"] = clamp(float(state.get("pressure_handling", pressure_handling)) + pressure_delta - pressure_impact * 0.08, *TEAM_STATE_BOUNDS["pressure_handling"])
    state["tactical_intensity"] = clamp(float(state.get("tactical_intensity", 1.0)) + tactical_delta, *TEAM_STATE_BOUNDS["tactical_intensity"])
    state["defensive_compactness"] = clamp(float(state.get("defensive_compactness", 1.0)) + compactness_delta, *TEAM_STATE_BOUNDS["defensive_compactness"])
    state["recovery_rate"] = clamp(float(state.get("recovery_rate", 1.0)) + recovery_delta - fatigue * 0.004, *TEAM_STATE_BOUNDS["recovery_rate"])
    return state