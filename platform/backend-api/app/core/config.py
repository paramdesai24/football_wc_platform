from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

CORE_DIR = Path(__file__).resolve().parent
APP_DIR = CORE_DIR.parent
PROJECT_ROOT = APP_DIR.parent


class Settings(BaseSettings):
    PROJECT_NAME: str = "FIFA WC 2026 Intelligence API"
    PROJECT_DESCRIPTION: str = "Advanced football intelligence, match prediction, and tournament simulation API."
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # SQLite Database (upgradeable to PostgreSQL)
    DATABASE_URL: str = f"sqlite:///{(PROJECT_ROOT / 'data' / 'fifa_wc_2026.db').as_posix()}"

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Logging
    LOG_LEVEL: str = "INFO"

    # ML
    MODEL_CACHE_DIR: str = str(PROJECT_ROOT / "model_cache")

    # Data
    DATA_DIR: str = str(PROJECT_ROOT.parent.parent / "DATA")

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
