"""
Football Intelligence Constants
================================
Calibrated constants for realistic football match prediction.
All values are derived from empirical international football data.

v2.0 — Recalibrated for xG separation, draw suppression,
       tactical profiles, and scoreline diversity.
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# PATH CONFIGURATION
# ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(os.path.abspath(__file__)).parents[2]  # c:\FIFA WC
DATA_DIR = PROJECT_ROOT / "platform" / "data" / "processed"
MATCH_ENGINE_DIR = PROJECT_ROOT / "match_engine"
EXPORTS_DIR = MATCH_ENGINE_DIR / "exports" / "output"
LOGS_DIR = MATCH_ENGINE_DIR / "logs"
DB_PATH = PROJECT_ROOT / "platform" / "data" / "football_intelligence.db"

# ─────────────────────────────────────────────────────────────
# DATA SOURCE FILES (Phase 2 outputs)
# ─────────────────────────────────────────────────────────────
ELO_FILE = DATA_DIR / "elo_ratings.csv"
ATTACK_DEFENSE_FILE = DATA_DIR / "attack_defense_ratings.csv"
FORM_FILE = DATA_DIR / "recent_form_rankings.csv"
SQUAD_FILE = DATA_DIR / "squad_strength_rankings.csv"
RANKINGS_FILE = DATA_DIR / "dynamic_world_rankings.csv"
EXPLAINABILITY_FILE = DATA_DIR / "ranking_explainability.csv"
COUNTRY_INTEL_FILE = DATA_DIR / "country_intelligence.csv"

# ─────────────────────────────────────────────────────────────
# FOOTBALL SCORING CONSTANTS
# ─────────────────────────────────────────────────────────────
# International football averages (empirical from 2018-2025 data)
BASE_GOALS_PER_TEAM = 1.35           # Average goals scored per team in international matches
INTL_TOTAL_GOALS_AVG = 2.70          # Average total goals per international match
HOME_ADVANTAGE_GOALS = 0.35          # Home advantage goal boost (standard venue)
NEUTRAL_VENUE_BOOST = 0.10           # Reduced home advantage at neutral venues (World Cup)
MAX_REALISTIC_XG = 3.2               # Cap expected goals (reduced from 4.0 for volatility control)
MIN_REALISTIC_XG = 0.40              # Floor to prevent near-zero expected goals (increased from 0.30)
MAX_SCORELINE = 7                    # Maximum individual team score to model (0-7 = 8 bins)

# ─────────────────────────────────────────────────────────────
# ELO SYSTEM CONSTANTS
# ─────────────────────────────────────────────────────────────
ELO_BASE = 1500                      # Elo system baseline rating
ELO_SCALE_FACTOR = 400               # Standard Elo scaling divisor
ELO_HOME_BONUS = 100                 # Elo-equivalent home advantage points
ELO_NEUTRAL_BONUS = 30               # Reduced bonus for neutral venues

# ─────────────────────────────────────────────────────────────
# DRAW PROBABILITY CONSTANTS
# ─────────────────────────────────────────────────────────────
# International football has ~24% draw rate (empirical)
BASE_DRAW_PROBABILITY = 0.22
DRAW_ELO_SENSITIVITY = 400           # Lower = draws decay faster with Elo gap
MAX_DRAW_PROBABILITY = 0.30          # Cap: even perfectly matched teams
MIN_DRAW_PROBABILITY = 0.06          # Floor: huge mismatches still rarely draw

# ─────────────────────────────────────────────────────────────
# PREDICTION WEIGHT CONFIGURATION
# ─────────────────────────────────────────────────────────────
# Weights for combining different intelligence signals
# Must sum to 1.0
PREDICTION_WEIGHTS = {
    "elo": 0.30,              # Historical Elo rating contribution
    "attack_defense": 0.25,   # Attack/defense rating differential
    "form": 0.20,             # Recent form and momentum
    "squad": 0.15,            # Squad overall quality
    "confederation": 0.10,   # Confederation strength effects
}

# ─────────────────────────────────────────────────────────────
# XG CALIBRATION (v3 — reduced volatility)
# ─────────────────────────────────────────────────────────────
# These control how much each factor CAN move xG away from baseline.
# Reduced power exponents and divisor to stabilize predictions.
XG_ATTACK_POWER = 1.2                # Nonlinear exponent for attack advantage (reduced from 1.4)
XG_DEFENSE_POWER = 1.1               # Nonlinear exponent for defensive suppression (reduced from 1.3)
XG_ELO_DIVISOR = 750.0               # Lower = Elo gap affects xG more strongly (reduced from 900)
XG_ELO_CLAMP = (0.75, 1.28)          # (min, max) Elo factor range (tightened from 0.72-1.32)
XG_FORM_SENSITIVITY = 0.30           # How much form moves xG (reduced from 0.40 for stability)
XG_SQUAD_SENSITIVITY = 0.22          # How much squad quality moves xG (reduced from 0.30)

# Observed data ranges (from Phase 2 analysis)
ATTACK_RATING_MEAN = 75.2
DEFENSE_RATING_MEAN = 83.0
ATTACK_RATING_MIN = 58.9
ATTACK_RATING_MAX = 95.9
DEFENSE_RATING_MIN = 56.1
DEFENSE_RATING_MAX = 100.0

# ─────────────────────────────────────────────────────────────
# TOURNAMENT IMPORTANCE MULTIPLIERS
# ─────────────────────────────────────────────────────────────
TOURNAMENT_IMPORTANCE = {
    "friendly": 1.0,
    "qualifier": 1.2,
    "nations_league": 1.3,
    "continental_group": 1.5,
    "continental_knockout": 1.7,
    "world_cup_group": 1.8,
    "world_cup_r16": 2.0,
    "world_cup_quarter": 2.2,
    "world_cup_semi": 2.4,
    "world_cup_final": 2.6,
}

# Tournament pressure effects on scoring (v2 — less compression)
TOURNAMENT_SCORING_MODIFIER = {
    "friendly": 1.05,           # Slightly more open play
    "qualifier": 1.00,          # Standard
    "nations_league": 0.98,     # Slightly cagier
    "continental_group": 0.97,  # Cautious but not suppressed
    "continental_knockout": 0.93,
    "world_cup_group": 0.96,    # WC groups are competitive but not ultra-tight
    "world_cup_r16": 0.90,      # Knockout tension reduces scoring
    "world_cup_quarter": 0.87,
    "world_cup_semi": 0.84,     # Semi-finals are tight
    "world_cup_final": 0.86,    # Finals can be tense or spectacular
}

# ─────────────────────────────────────────────────────────────
# HOME ADVANTAGE CONFIGURATION
# ─────────────────────────────────────────────────────────────
HOME_ADVANTAGE_CONFIG = {
    "home": {
        "elo_bonus": ELO_HOME_BONUS,
        "goal_boost": HOME_ADVANTAGE_GOALS,
        "win_prob_boost": 0.08,
    },
    "standard": {
        "elo_bonus": ELO_HOME_BONUS,
        "goal_boost": HOME_ADVANTAGE_GOALS,
        "win_prob_boost": 0.08,
    },
    "neutral": {
        "elo_bonus": ELO_NEUTRAL_BONUS,
        "goal_boost": NEUTRAL_VENUE_BOOST,
        "win_prob_boost": 0.02,
    },
    "away": {
        "elo_bonus": 0,
        "goal_boost": 0.0,
        "win_prob_boost": 0.0,
    },
}

# ─────────────────────────────────────────────────────────────
# CONFEDERATION INTELLIGENCE
# ─────────────────────────────────────────────────────────────
CONFEDERATION_STRENGTH = {
    "UEFA": 1.00,       # European football — deepest talent pool
    "CONMEBOL": 0.95,   # South American — elite efficiency
    "CONCACAF": 0.72,   # North/Central America — rising
    "AFC": 0.65,        # Asia — rapidly improving
    "CAF": 0.60,        # Africa — high variance, athletic
    "OFC": 0.40,        # Oceania — smallest pool
}

# Cross-confederation upset factors (higher = more upsets possible)
CONFEDERATION_UPSET_FACTOR = {
    "UEFA": 0.12,
    "CONMEBOL": 0.15,
    "CONCACAF": 0.20,
    "AFC": 0.22,
    "CAF": 0.25,        # African teams are unpredictable
    "OFC": 0.18,
}

# ─────────────────────────────────────────────────────────────
# TACTICAL PROFILES
# ─────────────────────────────────────────────────────────────
# Each team gets a tactical style that modifies xG and scoring patterns.
# attack_mod: multiplier for offensive xG (>1 = more attacking)
# defense_mod: multiplier applied to opponent's xG (>1 = leakier)
# draw_tendency: additive modifier to draw probability (-0.05 to +0.05)
# variance: scoring variance multiplier (higher = more unpredictable)
TACTICAL_PROFILES = {
    # South American flair
    "Brazil":       {"attack_mod": 1.15, "defense_mod": 0.92, "draw_tendency": -0.04, "variance": 1.15, "style": "attacking"},
    "Argentina":    {"attack_mod": 1.10, "defense_mod": 0.90, "draw_tendency": -0.03, "variance": 1.05, "style": "balanced_attack"},
    "Uruguay":      {"attack_mod": 1.02, "defense_mod": 0.88, "draw_tendency": 0.00,  "variance": 0.95, "style": "gritty"},
    "Colombia":     {"attack_mod": 1.08, "defense_mod": 0.95, "draw_tendency": -0.02, "variance": 1.10, "style": "attacking"},

    # European elite
    "France":       {"attack_mod": 1.12, "defense_mod": 0.90, "draw_tendency": -0.03, "variance": 1.08, "style": "balanced_attack"},
    "Spain":        {"attack_mod": 1.08, "defense_mod": 0.88, "draw_tendency": -0.02, "variance": 0.95, "style": "possession"},
    "Germany":      {"attack_mod": 1.12, "defense_mod": 0.95, "draw_tendency": -0.03, "variance": 1.12, "style": "attacking"},
    "England":      {"attack_mod": 1.05, "defense_mod": 0.90, "draw_tendency": -0.01, "variance": 1.00, "style": "balanced"},
    "Italy":        {"attack_mod": 0.95, "defense_mod": 0.82, "draw_tendency": 0.04,  "variance": 0.85, "style": "defensive"},
    "Netherlands":  {"attack_mod": 1.10, "defense_mod": 0.95, "draw_tendency": -0.02, "variance": 1.08, "style": "attacking"},
    "Portugal":     {"attack_mod": 1.08, "defense_mod": 0.90, "draw_tendency": -0.02, "variance": 1.05, "style": "balanced_attack"},
    "Belgium":      {"attack_mod": 1.06, "defense_mod": 0.93, "draw_tendency": -0.01, "variance": 1.05, "style": "balanced"},
    "Croatia":      {"attack_mod": 1.02, "defense_mod": 0.90, "draw_tendency": 0.02,  "variance": 0.92, "style": "balanced"},
    "Denmark":      {"attack_mod": 1.04, "defense_mod": 0.88, "draw_tendency": 0.00,  "variance": 0.95, "style": "structured"},
    "Switzerland":  {"attack_mod": 0.98, "defense_mod": 0.87, "draw_tendency": 0.03,  "variance": 0.88, "style": "defensive"},
    "Serbia":       {"attack_mod": 1.04, "defense_mod": 0.95, "draw_tendency": 0.00,  "variance": 1.00, "style": "balanced"},
    "Poland":       {"attack_mod": 1.00, "defense_mod": 0.92, "draw_tendency": 0.01,  "variance": 0.95, "style": "structured"},
    "Wales":        {"attack_mod": 0.95, "defense_mod": 0.90, "draw_tendency": 0.02,  "variance": 0.90, "style": "defensive"},
    "Scotland":     {"attack_mod": 0.98, "defense_mod": 0.93, "draw_tendency": 0.01,  "variance": 0.95, "style": "structured"},

    # CONCACAF
    "Mexico":       {"attack_mod": 1.04, "defense_mod": 0.92, "draw_tendency": 0.00,  "variance": 1.00, "style": "balanced"},
    "United States":{"attack_mod": 1.02, "defense_mod": 0.95, "draw_tendency": 0.00,  "variance": 1.02, "style": "balanced"},
    "Canada":       {"attack_mod": 1.00, "defense_mod": 0.95, "draw_tendency": 0.01,  "variance": 0.98, "style": "structured"},
    "Costa Rica":   {"attack_mod": 0.92, "defense_mod": 0.88, "draw_tendency": 0.04,  "variance": 0.85, "style": "defensive"},

    # AFC
    "Japan":        {"attack_mod": 1.04, "defense_mod": 0.88, "draw_tendency": 0.01,  "variance": 0.95, "style": "structured"},
    "South Korea":  {"attack_mod": 1.00, "defense_mod": 0.90, "draw_tendency": 0.01,  "variance": 0.95, "style": "structured"},
    "Australia":    {"attack_mod": 1.00, "defense_mod": 0.95, "draw_tendency": 0.00,  "variance": 1.00, "style": "balanced"},
    "Iran":         {"attack_mod": 0.98, "defense_mod": 0.88, "draw_tendency": 0.03,  "variance": 0.90, "style": "defensive"},
    "Saudi Arabia": {"attack_mod": 0.96, "defense_mod": 0.95, "draw_tendency": 0.01,  "variance": 1.05, "style": "balanced"},
    "India":        {"attack_mod": 0.88, "defense_mod": 1.05, "draw_tendency": 0.00,  "variance": 0.85, "style": "defensive"},
    "Qatar":        {"attack_mod": 0.94, "defense_mod": 0.98, "draw_tendency": 0.01,  "variance": 0.90, "style": "structured"},
    "China":        {"attack_mod": 0.90, "defense_mod": 1.02, "draw_tendency": 0.00,  "variance": 0.88, "style": "defensive"},

    # CAF
    "Morocco":      {"attack_mod": 1.00, "defense_mod": 0.85, "draw_tendency": 0.02,  "variance": 0.95, "style": "defensive"},
    "Senegal":      {"attack_mod": 1.05, "defense_mod": 0.92, "draw_tendency": -0.01, "variance": 1.05, "style": "balanced"},
    "Nigeria":      {"attack_mod": 1.06, "defense_mod": 0.98, "draw_tendency": -0.02, "variance": 1.12, "style": "attacking"},
    "Ghana":        {"attack_mod": 1.04, "defense_mod": 0.98, "draw_tendency": -0.01, "variance": 1.08, "style": "attacking"},
    "Cameroon":     {"attack_mod": 1.04, "defense_mod": 1.00, "draw_tendency": -0.01, "variance": 1.10, "style": "attacking"},
    "Algeria":      {"attack_mod": 1.02, "defense_mod": 0.92, "draw_tendency": 0.01,  "variance": 1.00, "style": "balanced"},
    "Tunisia":      {"attack_mod": 0.96, "defense_mod": 0.88, "draw_tendency": 0.03,  "variance": 0.90, "style": "defensive"},
    "Egypt":        {"attack_mod": 1.00, "defense_mod": 0.92, "draw_tendency": 0.01,  "variance": 0.95, "style": "balanced"},

    # South American others
    "Chile":        {"attack_mod": 1.04, "defense_mod": 0.95, "draw_tendency": -0.01, "variance": 1.05, "style": "pressing"},
    "Peru":         {"attack_mod": 0.98, "defense_mod": 0.92, "draw_tendency": 0.01,  "variance": 0.95, "style": "structured"},
    "Ecuador":      {"attack_mod": 1.02, "defense_mod": 0.95, "draw_tendency": 0.00,  "variance": 1.02, "style": "balanced"},
    "Paraguay":     {"attack_mod": 0.96, "defense_mod": 0.90, "draw_tendency": 0.02,  "variance": 0.92, "style": "gritty"},
    "Bolivia":      {"attack_mod": 0.90, "defense_mod": 1.05, "draw_tendency": 0.00,  "variance": 0.85, "style": "defensive"},
}

# Default tactical profile for unlisted teams
DEFAULT_TACTICAL_PROFILE = {
    "attack_mod": 1.00, "defense_mod": 1.00, "draw_tendency": 0.00,
    "variance": 1.00, "style": "balanced",
}

# ─────────────────────────────────────────────────────────────
# DIXON-COLES DRAW ADJUSTMENT
# ─────────────────────────────────────────────────────────────
# The Dixon-Coles model corrects Poisson's over-prediction of draws
# by adjusting 0-0, 1-0, 0-1, and 1-1 probabilities.
# rho < 0 suppresses 0-0 and 1-1, boosts 1-0 and 0-1.
DIXON_COLES_RHO = -0.13             # Empirical: international football ~-0.10 to -0.15

# ─────────────────────────────────────────────────────────────
# MONTE CARLO SIMULATION
# ─────────────────────────────────────────────────────────────
DEFAULT_SIMULATIONS = 10_000         # Default number of Monte Carlo iterations
MAX_SIMULATIONS = 100_000            # Maximum allowed simulations
SIMULATION_SEED = 2026               # Reproducibility seed

# ─────────────────────────────────────────────────────────────
# CONFIDENCE SCORING
# ─────────────────────────────────────────────────────────────
CONFIDENCE_THRESHOLDS = {
    "very_high": 0.85,
    "high": 0.70,
    "medium": 0.50,
    "low": 0.30,
    "very_low": 0.0,
}

# ─────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
