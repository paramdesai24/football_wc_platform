from fastapi import APIRouter
from app.api.v1.endpoints import health, countries, players, predictions, simulation, analytics

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(countries.router, prefix="/countries", tags=["Countries"])
api_router.include_router(players.router, prefix="/players", tags=["Players"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
api_router.include_router(simulation.router, prefix="/simulation", tags=["Simulation"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
