from fastapi import APIRouter
from datetime import datetime
from app.core.config import settings
import pandas as pd
from pathlib import Path

# Paths used by health checks
CURRENT_FILE = Path(__file__).resolve()
DATA_PATH = CURRENT_FILE.parents[5] / "data" / "processed"
RANKINGS_FILE = DATA_PATH / "dynamic_world_rankings_active.csv"


router = APIRouter()


@router.get("/health")
async def health_check():
    # Check if data is available
    data_available = RANKINGS_FILE.exists()
    
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "data_available": data_available,
        "endpoints": {
            "predictions": "ready",
            "rankings": "ready" if data_available else "no_data",
            "analytics": "ready" if data_available else "no_data",
            "simulation": "ready" if data_available else "no_data",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/ready")
async def readiness_check():
    try:
        data_available = RANKINGS_FILE.exists()
    except Exception:
        data_available = False

    return {
        "status": "ready" if data_available else "degraded",
        "checks": {
            "api": True,
            "database": data_available,
            "ml_models": False,
            "data_pipeline": data_available,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
