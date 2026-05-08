"""
Constants for the Football Intelligence Data Pipeline.
"""

from typing import Dict, Set
from pathlib import Path

# Root directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "DATA"
PIPELINE_DIR = PROJECT_ROOT / "platform" / "data-pipeline"
PROCESSED_DATA_DIR = PROJECT_ROOT / "platform" / "data" / "processed"
LOGS_DIR = PIPELINE_DIR / "logs"

# Ensure directories exist
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Dataset paths
DATASETS = {
    "players": DATA_DIR / "transfer market" / "players.csv",
    "player_valuations": DATA_DIR / "transfer market" / "player_valuations.csv",
    "appearances": DATA_DIR / "transfer market" / "appearances.csv",
    "games": DATA_DIR / "transfer market" / "games.csv",
    "game_events": DATA_DIR / "transfer market" / "game_events.csv",
    "game_lineups": DATA_DIR / "transfer market" / "game_lineups.csv",
    "transfers": DATA_DIR / "transfer market" / "transfers.csv",
    "clubs": DATA_DIR / "transfer market" / "clubs.csv",
    "competitions": DATA_DIR / "transfer market" / "competitions.csv",
    "national_teams": DATA_DIR / "transfer market" / "national_teams.csv",
    "results": DATA_DIR / "intl results" / "results.csv",
    "goalscorers": DATA_DIR / "intl results" / "goalscorers.csv",
    "shootouts": DATA_DIR / "intl results" / "shootouts.csv",
    "players_light_2025_26": DATA_DIR / "latest" / "players_data_light-2025_2026.csv",
    "players_full_2025_26": DATA_DIR / "latest" / "players_data-2025_2026.csv",
}

# Output paths
OUTPUT_DATASETS = {
    "master_players": PROCESSED_DATA_DIR / "master_players.csv",
    "master_countries": PROCESSED_DATA_DIR / "master_countries.csv",
    "player_form": PROCESSED_DATA_DIR / "player_form.csv",
    "country_strength": PROCESSED_DATA_DIR / "country_strength.csv",
    "squad_aggregates": PROCESSED_DATA_DIR / "squad_aggregates.csv",
    "audit_report": LOGS_DIR / "audit_report.json",
    "cleaning_report": LOGS_DIR / "cleaning_report.json",
    "feature_report": LOGS_DIR / "feature_report.json",
}

# Database (centralized under platform/data/processed)
DATABASE_PATH = PROCESSED_DATA_DIR / "football_intelligence.db"

# Player positions (FIFA standard)
POSITIONS = {
    "GK": "Goalkeeper",
    "CB": "Center Back",
    "LB": "Left Back",
    "RB": "Right Back",
    "LWB": "Left Wing Back",
    "RWB": "Right Wing Back",
    "DM": "Defensive Midfielder",
    "CM": "Central Midfielder",
    "AM": "Attacking Midfielder",
    "LM": "Left Midfielder",
    "RM": "Right Midfielder",
    "LW": "Left Winger",
    "RW": "Right Winger",
    "CF": "Center Forward",
    "ST": "Striker",
    "FW": "Forward",
}

# Confederations
CONFEDERATIONS = {
    "UEFA": "Europe",
    "CONMEBOL": "South America",
    "CONCACAF": "North/Central America",
    "CAF": "Africa",
    "AFC": "Asia",
    "OFC": "Oceania",
}

# Top-tier competitions (for weighting)
TOP_COMPETITIONS = {
    "UEFA Champions League",
    "UEFA Europa League",
    "Premier League",
    "La Liga",
    "Serie A",
    "Bundesliga",
    "Ligue 1",
}

# Country name mappings (normalize inconsistencies)
COUNTRY_MAPPINGS = {
    "England": "England",
    "Scotland": "Scotland",
    "Wales": "Wales",
    "Northern Ireland": "Northern Ireland",
    "United States": "United States",
    "United States of America": "United States",
    "USA": "United States",
    "South Korea": "South Korea",
    "Korea": "South Korea",
    "Czech Republic": "Czechia",
    "Republic of Ireland": "Ireland",
    "Côte d'Ivoire": "Ivory Coast",
    "Cote d'Ivoire": "Ivory Coast",
    "Bosnia-Herzegovina": "Bosnia and Herzegovina",
    "Bosnia and Herzegowina": "Bosnia and Herzegovina",
    "DR Congo": "Democratic Republic of the Congo",
    "Congo": "Democratic Republic of the Congo",
    "Central African Republic": "Central African Republic",
    "St. Lucia": "Saint Lucia",
    "St Lucia": "Saint Lucia",
    "Antigua and Barbuda": "Antigua and Barbuda",
    "Trinidad & Tobago": "Trinidad and Tobago",
    "Trinidad and Tobago": "Trinidad and Tobago",
    "Sao Tome and Principe": "São Tomé and Príncipe",
}

# Feature engineering weights
RECENCY_WEIGHTS = {
    "recent_2025_26": 0.5,      # 2025-26 season (most recent)
    "current_season": 0.3,      # Current season historical
    "historical": 0.2,           # Historical average
}

# Min/max thresholds for validation
MIN_PLAYER_APPEARANCES = 5
MIN_COUNTRY_MATCHES = 5
MAX_MARKET_VALUE = 1_000_000_000  # 1 billion

# Date thresholds
RECENT_MATCH_DAYS = 365  # Last 365 days is "recent"

# Logging
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Processing
BATCH_SIZE = 1000
RANDOM_SEED = 42

print(f"✓ Constants loaded from {PROJECT_ROOT}")
print(f"  Data directory: {DATA_DIR}")
print(f"  Pipeline directory: {PIPELINE_DIR}")
