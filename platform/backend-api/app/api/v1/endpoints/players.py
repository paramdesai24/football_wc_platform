"""
Players endpoint — DEPRECATED.

Player-level simulation has been removed from the platform.
The project operates at team-level intelligence only.
These stub endpoints remain for API compatibility but return
deprecation notices.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_players():
    return {
        "data": [],
        "total": 0,
        "message": "Player-level features have been removed. The platform operates at team-level intelligence only.",
    }


@router.get("/{player_id}")
async def get_player(player_id: str):
    return {
        "data": None,
        "message": "Player-level features have been removed. The platform operates at team-level intelligence only.",
    }
