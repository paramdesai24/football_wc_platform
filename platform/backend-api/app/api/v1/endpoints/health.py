from fastapi import APIRouter
from datetime import datetime
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health/ready")
async def readiness_check():
    return {
        "status": "ready",
        "checks": {
            "api": True,
            "database": False,
            "ml_models": False,
        },
        "timestamp": datetime.utcnow().isoformat(),
    }
