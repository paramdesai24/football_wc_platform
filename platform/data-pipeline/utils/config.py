"""Configuration module for pipeline paths and settings.

This centralizes dataset paths, processed-data paths, database paths, weights,
and logging configuration. It is intended to be imported by run scripts and
controllers; existing modules may continue to use `utils.constants`.
"""

from pathlib import Path
from typing import Dict

# Get pipeline root (parent of utils)
UTILS_DIR = Path(__file__).resolve().parent
PIPELINE_DIR = UTILS_DIR.parent
PROJECT_ROOT = PIPELINE_DIR.parent.parent

# Data architecture: keep raw data in project DATA (existing) and processed outputs here
RAW_DATA_DIR = PROJECT_ROOT / "DATA"
PROCESSED_DIRS = {
    # Centralize all final processed outputs under platform/data/processed
    "pipeline_processed": PROJECT_ROOT / "platform" / "data" / "processed",
    "project_processed": PROJECT_ROOT / "platform" / "data" / "processed",
}

# Ensure processed directories exist
for p in PROCESSED_DIRS.values():
    p.mkdir(parents=True, exist_ok=True)

# Logs
LOGS_DIR = PIPELINE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# SQLite database path (centralized)
DATABASE_PATH = PROCESSED_DIRS["pipeline_processed"] / "football_intelligence.db"

# Recency weights (defaults, can be overridden)
RECENCY_WEIGHTS = {
    "recent_2025_26": 0.5,
    "current_season": 0.3,
    "historical": 0.2,
}

# Export config
EXPORT_CSV_OPTIONS = {"index": False}

# Logging config
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

def get_processed_paths() -> Dict[str, Path]:
    return PROCESSED_DIRS
