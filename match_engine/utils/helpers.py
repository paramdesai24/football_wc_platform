"""
Helper Utilities
=================
Common helper functions for the match prediction engine.
"""

import re
import logging
from typing import Union

logger = logging.getLogger("match_engine.helpers")

# ─────────────────────────────────────────────────────────────
# TEAM NAME ALIASES (common alternative spellings)
# ─────────────────────────────────────────────────────────────
TEAM_NAME_ALIASES = {
    "usa": "united states",
    "us": "united states",
    "america": "united states",
    "usmnt": "united states",
    "uk": "england",
    "korea": "south korea",
    "korea republic": "south korea",
    "rep. of ireland": "republic of ireland",
    "rep of ireland": "republic of ireland",
    "bosnia": "bosnia and herzegovina",
    "bosnia-herzegovina": "bosnia and herzegovina",
    "trinidad": "trinidad and tobago",
    "czechia": "czech republic",
    "côte d'ivoire": "ivory coast",
    "cote d'ivoire": "ivory coast",
    "dr congo": "congo dr",
    "democratic republic of congo": "congo dr",
    "uae": "united arab emirates",
    "china": "china pr",
    "hong kong": "hong kong, china",
    "north korea": "korea dpr",
    "dpr korea": "korea dpr",
    "ir iran": "iran",
    "cabo verde": "cape verde",
    "swaziland": "eswatini",
    "burma": "myanmar",
    "holland": "netherlands",
    "the netherlands": "netherlands",
}


def normalize_team_name(name: str) -> str:
    """
    Normalize a team name for lookup.
    Handles common aliases, case, and whitespace.
    """
    if not name:
        return ""
    cleaned = name.strip().lower()
    cleaned = re.sub(r'\s+', ' ', cleaned)
    # Check alias table
    return TEAM_NAME_ALIASES.get(cleaned, cleaned)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value to [min_val, max_val]."""
    return max(min_val, min(max_val, value))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safe division that returns default on zero/NaN denominator."""
    if denominator == 0 or denominator != denominator:  # NaN check
        return default
    return numerator / denominator


def format_probability(prob: float) -> str:
    """Format a probability as a percentage string."""
    return f"{prob * 100:.1f}%"


def format_scoreline(home: str, away: str, home_goals: int, away_goals: int) -> str:
    """Format a scoreline string."""
    return f"{home} {home_goals}-{away_goals} {away}"


def rating_tier(rating: float) -> str:
    """Classify a team's overall rating into a tier."""
    if rating >= 0.85:
        return "Elite"
    elif rating >= 0.70:
        return "Strong"
    elif rating >= 0.55:
        return "Competitive"
    elif rating >= 0.40:
        return "Developing"
    else:
        return "Emerging"


def elo_tier(elo: float) -> str:
    """Classify a team by Elo rating."""
    if elo >= 2000:
        return "Elite"
    elif elo >= 1800:
        return "Strong"
    elif elo >= 1600:
        return "Competitive"
    elif elo >= 1400:
        return "Developing"
    else:
        return "Emerging"


def match_type_label(importance: str) -> str:
    """Human-readable match type label."""
    labels = {
        "friendly": "International Friendly",
        "qualifier": "World Cup Qualifier",
        "nations_league": "Nations League",
        "continental_group": "Continental Championship — Group Stage",
        "continental_knockout": "Continental Championship — Knockout",
        "world_cup_group": "FIFA World Cup — Group Stage",
        "world_cup_r16": "FIFA World Cup — Round of 16",
        "world_cup_quarter": "FIFA World Cup — Quarter-Final",
        "world_cup_semi": "FIFA World Cup — Semi-Final",
        "world_cup_final": "FIFA World Cup — Final",
    }
    return labels.get(importance, importance.replace("_", " ").title())
