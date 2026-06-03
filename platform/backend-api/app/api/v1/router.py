from fastapi import APIRouter
from app.api.v1.endpoints import health, countries, players, predictions, simulation, analytics, tournament, auction_players, leagues, rooms, match_admin, auth

api_router = APIRouter()
api_router.include_router(countries.router, prefix="/countries", tags=["Countries"])
api_router.include_router(players.router, prefix="/players", tags=["Players (Deprecated)"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
api_router.include_router(simulation.router, prefix="/simulation", tags=["Simulation"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(tournament.router, tags=["Tournament"])
api_router.include_router(auction_players.router)
api_router.include_router(leagues.router)
api_router.include_router(rooms.router)
api_router.include_router(match_admin.router)
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

