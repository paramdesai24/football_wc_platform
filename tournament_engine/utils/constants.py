"""
Tournament Engine Constants
==============================
Configuration for FIFA World Cup 2026 tournament simulation.
48-team format: 12 groups of 4, top 2 + 8 best 3rd advance to R32.
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(os.path.abspath(__file__)).parents[2]  # c:\FIFA WC
TOURNAMENT_DIR = PROJECT_ROOT / "tournament_engine"
FIXTURES_DIR = TOURNAMENT_DIR / "fixtures"
EXPORTS_DIR = TOURNAMENT_DIR / "exports"
LOGS_DIR = TOURNAMENT_DIR / "logs"
DB_PATH = PROJECT_ROOT / "platform" / "data" / "football_intelligence.db"

TEAMS_FILE = FIXTURES_DIR / "world_cup_2026_teams.csv"
GROUPS_FILE = FIXTURES_DIR / "world_cup_2026_groups.csv"
GROUP_FIXTURES_FILE = FIXTURES_DIR / "world_cup_2026_group_fixtures.csv"

# ─────────────────────────────────────────────────────────────
# TOURNAMENT FORMAT
# ─────────────────────────────────────────────────────────────
TOTAL_TEAMS = 48
TOTAL_GROUPS = 12
TEAMS_PER_GROUP = 4
GROUP_MATCHDAYS = 3
MATCHES_PER_GROUP = 6  # C(4,2) = 6 round-robin matches
AUTO_ADVANCE = 2       # Top 2 from each group advance automatically
BEST_THIRD = 8         # 8 best 3rd-place teams also advance
KNOCKOUT_TEAMS = 32    # 24 auto + 8 best-third = 32

GROUP_NAMES = [chr(65 + i) for i in range(TOTAL_GROUPS)]  # A-L

# ─────────────────────────────────────────────────────────────
# POINTS SYSTEM
# ─────────────────────────────────────────────────────────────
POINTS_WIN = 3
POINTS_DRAW = 1
POINTS_LOSS = 0

# ─────────────────────────────────────────────────────────────
# FIFA TIEBREAKER ORDER (within group)
# ─────────────────────────────────────────────────────────────
# 1. Points (higher)
# 2. Goal difference (higher)
# 3. Goals scored (higher)
# 4. Points in head-to-head matches
# 5. Goal difference in head-to-head
# 6. Goals scored in head-to-head
# 7. Fair play points (lower yellow/red cards)
# 8. Drawing of lots

# ─────────────────────────────────────────────────────────────
# KNOCKOUT BRACKET (FIFA 2026 format)
# ─────────────────────────────────────────────────────────────
# Round of 32: 16 matches
# The bracket connects group winners (1st), runners-up (2nd),
# and best 3rd-place qualifiers based on a pre-defined mapping.
#
# FIFA bracket structure for 48-team format:
# Match 1:  1A vs 3C/D/E
# Match 2:  2C vs 2D
# Match 3:  1B vs 3A/E/F
# Match 4:  2E vs 2F
# Match 5:  1C vs 3B/G/H
# Match 6:  2A vs 2B
# Match 7:  1D vs 3F/I/J
# Match 8:  2G vs 2H
# Match 9:  1E vs 3A/B/C
# Match 10: 2I vs 2J
# Match 11: 1F vs 3D/H/I
# Match 12: 2K vs 2L
# Match 13: 1G vs 3E/J/K
# Match 14: 1H vs 3G/K/L
# Match 15: 1I vs 3J/K/L
# (adjusted based on which third-place teams qualify)
#
# We use a simplified deterministic mapping below.

# R32 bracket: (slot_home, slot_away)
# Format: "1X" = Winner of Group X, "2X" = Runner-up of Group X
# "3_N" = Nth best 3rd-place team (resolved at runtime)
R32_BRACKET_TEMPLATE = [
    # Left half of bracket
    ("1A", "3_1"),   # Match 1
    ("2C", "2D"),    # Match 2
    ("1B", "3_2"),   # Match 3
    ("2E", "2F"),    # Match 4
    ("1C", "3_3"),   # Match 5
    ("2A", "2B"),    # Match 6
    ("1D", "3_4"),   # Match 7
    ("2G", "2H"),    # Match 8
    # Right half of bracket
    ("1E", "3_5"),   # Match 9
    ("2I", "2J"),    # Match 10
    ("1F", "3_6"),   # Match 11
    ("2K", "2L"),    # Match 12
    ("1G", "3_7"),   # Match 13
    ("1H", "3_8"),   # Match 14
    ("1I", "2I"),    # Match 15 — adjusted
    ("1J", "2J"),    # Match 16 — adjusted
]

# R16: Winners of R32 pairs
R16_PAIRS = [
    (0, 1),    # Winner M1 vs Winner M2
    (2, 3),    # Winner M3 vs Winner M4
    (4, 5),    # Winner M5 vs Winner M6
    (6, 7),    # Winner M7 vs Winner M8
    (8, 9),    # Winner M9 vs Winner M10
    (10, 11),  # Winner M11 vs Winner M12
    (12, 13),  # Winner M13 vs Winner M14
    (14, 15),  # Winner M15 vs Winner M16
]

# QF: Winners of R16 pairs
QF_PAIRS = [(0, 1), (2, 3), (4, 5), (6, 7)]

# SF: Winners of QF pairs
SF_PAIRS = [(0, 1), (2, 3)]

# ─────────────────────────────────────────────────────────────
# EXTRA TIME & PENALTY CONFIGURATION
# ─────────────────────────────────────────────────────────────
EXTRA_TIME_SCORING_FACTOR = 0.80    # xG multiplier for ET (Phase 4.2d: raised so
                                    #   more ET matches are decided in extra time,
                                    #   fewer cascade to penalty shootouts)
EXTRA_TIME_MINUTES_RATIO = 30 / 90  # 30 min / 90 min
PENALTY_BASE_SCORE_PROB = 0.75       # Base probability of scoring a penalty
PENALTY_ROUNDS = 5                    # Standard 5-round shootout
PENALTY_SUDDEN_DEATH_MAX = 10        # Max additional sudden-death rounds
PENALTY_ELO_SENSITIVITY = 500        # How Elo gap affects penalty scoring
PENALTY_CONFIDENCE_WEIGHT = 0.15     # How confidence score affects penalties

# ─────────────────────────────────────────────────────────────
# MONTE CARLO
# ─────────────────────────────────────────────────────────────
DEFAULT_MC_SIMULATIONS = 1000
MAX_MC_SIMULATIONS = 10000
MC_SEED = 2026

# ─────────────────────────────────────────────────────────────
# HOST CONTINENT BOOST
# ─────────────────────────────────────────────────────────────
# Subtle boost for CONCACAF teams playing in North America
HOST_CONTINENT_XG_BOOST = 0.08     # Additional xG for host-continent teams
HOST_CONFEDERATION = "CONCACAF"

# ─────────────────────────────────────────────────────────────
# TEAM NAME ALIASES
# ─────────────────────────────────────────────────────────────
# Maps tournament names to Phase 2 data names
TEAM_NAME_ALIASES = {
    "Czechia": "Czech Republic",
    "Türkiye": "Turkey",
    "Curaçao": "Curacao",
    "Cabo Verde": "Cape Verde",
    "Korea Republic": "South Korea",
    "IR Iran": "Iran",
    "Côte d'Ivoire": "Ivory Coast",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
}

# ─────────────────────────────────────────────────────────────
# REALISM CALIBRATION (PHASE 4.2 — FINAL POLISH)
# ─────────────────────────────────────────────────────────────

# Elite Teams (Traditional Powers + Current Giants)
ELITE_TEAMS = {
    "Brazil", "France", "Argentina", "Spain", "England",
    "Germany", "Portugal", "Netherlands", "Italy", "Belgium"
}

# Tournament Experience/Pedigree Modifier (Historical success factor)
# Maps team -> composure xG boost in high-pressure rounds (subtle)
TOURNAMENT_PEDIGREE = {
    "Brazil":      0.06,   # 5 Titles — attacking fluency
    "Germany":     0.06,   # 4 Titles — clinical finishing
    "Argentina":   0.05,   # 3 Titles — winning mentality
    "France":      0.05,   # 2 Titles — elite depth
    "Spain":       0.04,   # 1 Title  — positional dominance
    "England":     0.03,   # 1 Title  — tournament experience
    "Uruguay":     0.04,   # 2 Titles — punching above weight
    "Netherlands": 0.03,   # Consistent deep runs
    "Portugal":    0.03,
    "Italy":       0.06,   # 4 Titles
    "Croatia":     0.02,   # Proven knockout pedigree
}

# ── TACTICAL TEAM IDENTITIES ──────────────────────────────────
# Each dict entry: (xg_multiplier, draw_affinity, defensive_solidity)
# xg_multiplier: scales the raw Phase-3 xG (>1 = attack-heavy, <1 = defensive)
# draw_affinity: extra probability mass added to draw outcome [0–0.10]
# defensive_solidity: reduces opponent xG [0–0.15]
TEAM_STYLE = {
    # High-Attacking (Brazil-style)
    "Brazil":       {"xg_mult": 1.10, "draw_affinity": 0.00, "def_solid": 0.05},
    # Technical possession (Spain/France-style)
    "Spain":        {"xg_mult": 1.00, "draw_affinity": 0.02, "def_solid": 0.08},
    "France":       {"xg_mult": 1.05, "draw_affinity": 0.01, "def_solid": 0.07},
    # Structured control (England)
    "England":      {"xg_mult": 0.95, "draw_affinity": 0.03, "def_solid": 0.09},
    # Technical attack (Portugal/Argentina)
    "Portugal":     {"xg_mult": 1.05, "draw_affinity": 0.01, "def_solid": 0.05},
    "Argentina":    {"xg_mult": 1.02, "draw_affinity": 0.02, "def_solid": 0.06},
    # Power football (Germany)
    "Germany":      {"xg_mult": 1.08, "draw_affinity": 0.01, "def_solid": 0.06},
    # Total Football (Netherlands)
    "Netherlands":  {"xg_mult": 1.05, "draw_affinity": 0.01, "def_solid": 0.05},
    # Resilient knockout teams (Croatia, Japan, Morocco-style)
    "Croatia":      {"xg_mult": 0.88, "draw_affinity": 0.05, "def_solid": 0.12},
    "Japan":        {"xg_mult": 0.85, "draw_affinity": 0.04, "def_solid": 0.11},
    "Morocco":      {"xg_mult": 0.80, "draw_affinity": 0.05, "def_solid": 0.14},
    "Switzerland":  {"xg_mult": 0.90, "draw_affinity": 0.04, "def_solid": 0.10},
    "Mexico":       {"xg_mult": 0.92, "draw_affinity": 0.03, "def_solid": 0.08},
    "South Korea":  {"xg_mult": 0.88, "draw_affinity": 0.03, "def_solid": 0.09},
    "Senegal":      {"xg_mult": 0.92, "draw_affinity": 0.03, "def_solid": 0.08},
    "Uruguay":      {"xg_mult": 0.95, "draw_affinity": 0.03, "def_solid": 0.09},
    "Iran":         {"xg_mult": 0.78, "draw_affinity": 0.05, "def_solid": 0.13},
    "Algeria":      {"xg_mult": 0.85, "draw_affinity": 0.04, "def_solid": 0.10},
    "Ivory Coast":  {"xg_mult": 0.95, "draw_affinity": 0.02, "def_solid": 0.06},
    "Colombia":     {"xg_mult": 0.93, "draw_affinity": 0.02, "def_solid": 0.07},
    "Belgium":      {"xg_mult": 1.00, "draw_affinity": 0.02, "def_solid": 0.06},
}
# Default style for unlisted teams
DEFAULT_TEAM_STYLE = {"xg_mult": 0.90, "draw_affinity": 0.03, "def_solid": 0.07}

# ── PENALTY SPECIALIST PROFILES ───────────────────────────────
# Positive = overperform in shootouts, Negative = underperform
# Absolute values kept small (± 0.04 max) for realism
PENALTY_SPECIALIST = {
    "Croatia":     +0.04,   # Ice-cold penalty takers
    "Argentina":   +0.03,   # Pressure-hardened (Messi era)
    "Germany":     +0.03,   # Clinical engineering
    "Spain":       +0.02,   # Technical precision
    "Brazil":      +0.01,   # Historically mixed but quality
    "England":     -0.03,   # Historically poor penalty record
    "France":      +0.01,
    "Netherlands": -0.01,
    "Portugal":    +0.02,
    "Japan":       +0.01,   # Well-drilled
    "Morocco":     +0.01,
    "Senegal":     -0.01,
    "Switzerland": +0.01,
}

# ── STAGE-SPECIFIC GOAL CAPS ──────────────────────────────────
# Prevents absurd blowouts in tight knockout football
# (home_cap, away_cap) — rare for any KO game to exceed
STAGE_GOAL_CAP = {
    "R32":       (5, 5),
    "R16":       (5, 5),
    "QF":        (4, 4),
    "SF":        (3, 3),
    "3rd_place": (4, 4),
    "Final":     (3, 3),
}

# ── STAGE VOLATILITY SCALING ──────────────────────────────────
# 1.0 = base Poisson variance, < 1.0 = quality-favoring
# Recalibrated (Phase 4.2): slightly more open than 4.1 to allow
# controlled upsets while still respecting pedigree
STAGE_VOLATILITY_SCALING = {
    "GS":        1.00,   # Group Stage — full variance
    "R32":       0.95,   # R32 — mild stabilisation
    "R16":       0.88,   # R16 — quality matters
    "QF":        0.80,   # QF  — controlled but tense
    "SF":        0.74,   # SF  — elite dominance, drama allowed
    "3rd_place": 0.85,
    "Final":     0.70,   # Final — quality triumphs, tight game
}

# ── ET PROBABILITY AMPLIFICATION PER STAGE ───────────────────
# Calibrated (Phase 4.2c): targeting ~20-25% ET, ~8-12% penalties
STAGE_ET_BOOST = {
    "R32":       0.01,
    "R16":       0.02,
    "QF":        0.03,
    "SF":        0.04,
    "3rd_place": 0.02,
    "Final":     0.05,
}

# ── TACTICAL COMPRESSION FACTOR FOR BALANCED MATCHUPS ─────────
# When |home_xg - away_xg| < threshold, compress both lambdas
# toward a cautious tactical midpoint to increase draw probability
TACTICAL_BALANCE_THRESHOLD = 0.30  # xG gap below which game is "balanced"
TACTICAL_COMPRESSION_RATE  = 0.08  # Reduced from 0.12 — fine-tuned for realism

# ── KNOCKOUT FATIGUE ──────────────────────────────────────────
# Reduces effective xG as teams progress deeper (in addition to ET drain)
# Simulates physical + psychological fatigue across the bracket
ROUND_FATIGUE_FACTOR = {
    "R32":       1.00,
    "R16":       0.97,
    "QF":        0.94,
    "SF":        0.91,
    "3rd_place": 0.89,
    "Final":     0.88,
}

# ── REGULATION DRAW RESOLUTION ───────────────────────────────
# When Poisson produces a regulation draw, this is the probability
# that a late decisive goal breaks the tie (match decided in 90 min).
# 0.32 = 32% chance of late winner; 68% of reg draws proceed to ET.
# At natural draw rate ~25-28%, this yields ~17-19% ET across KO.
# Combined with higher ET xG (0.80), fewer ET games cascade to pens.
REGULATION_DRAW_BREAK_PROB = 0.32

# ── EXTRA TIME DRAW RESOLUTION ───────────────────────────────
# When ET produces a draw, this is the probability of a decisive
# golden-moment goal breaking the deadlock before penalties.
# 0.30 = 30% of ET draws resolved in ET; 70% go to penalties.
# Targets penalties at ~10-11% of all KO matches.
ET_DRAW_BREAK_PROB = 0.30

# Non-elite teams in QF+ face regression toward mean (fatigue+pressure)
DARK_HORSE_REGRESSION_FACTOR = 0.92   # Slightly less punishing than 4.1

# ── PENALTY ENGINE ────────────────────────────────────────────
PENALTY_ELITE_BOOST   = 0.04          # Reduced from 0.06 — more parity
PENALTY_BASE_SCORE_PROB = 0.76        # FIFA real-world historical rate


# ─────────────────────────────────────────────────────────────
# STADIUM DATA (representative venues per host city)
# ─────────────────────────────────────────────────────────────
HOST_VENUES = {
    "A": [("Estadio Azteca", "Mexico City"), ("Estadio Akron", "Guadalajara")],
    "B": [("BMO Field", "Toronto"), ("BC Place", "Vancouver")],
    "C": [("MetLife Stadium", "East Rutherford"), ("Hard Rock Stadium", "Miami")],
    "D": [("AT&T Stadium", "Dallas"), ("NRG Stadium", "Houston")],
    "E": [("Mercedes-Benz Stadium", "Atlanta"), ("Lincoln Financial Field", "Philadelphia")],
    "F": [("Lumen Field", "Seattle"), ("Levi's Stadium", "San Francisco")],
    "G": [("SoFi Stadium", "Los Angeles"), ("Estadio BBVA", "Monterrey")],
    "H": [("Arrowhead Stadium", "Kansas City"), ("Gillette Stadium", "Foxborough")],
    "I": [("MetLife Stadium", "East Rutherford"), ("Mercedes-Benz Stadium", "Atlanta")],
    "J": [("Hard Rock Stadium", "Miami"), ("AT&T Stadium", "Dallas")],
    "K": [("SoFi Stadium", "Los Angeles"), ("Lumen Field", "Seattle")],
    "L": [("Gillette Stadium", "Foxborough"), ("Lincoln Financial Field", "Philadelphia")],
}

# ─────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s | %(name)-30s | %(levelname)-7s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
