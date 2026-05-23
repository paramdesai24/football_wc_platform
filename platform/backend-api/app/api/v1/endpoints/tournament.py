from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Any

from app.services.tournament_service import get_tournament_results, override_match, resimulate_from_match
from app.services.advanced_tournament_service import play_as_team


router = APIRouter()


class OverrideMatchRequest(BaseModel):
    match_id: Any
    home_score: int = Field(..., ge=0)
    away_score: int = Field(..., ge=0)
    penalties_winner: Optional[str] = Field(default=None, pattern="^(home|away)$")


class ResimulateRequest(BaseModel):
    match_id: Any


class PlayAsRequest(BaseModel):
    team_name: str = Field(..., min_length=2)
    simulations: int = Field(default=10, ge=1, le=25)
    seed: int = Field(default=2026)


@router.get("/tournament_results")
async def tournament_results(refresh: bool = False, simulations: Optional[int] = None):
    try:
        return {"data": get_tournament_results(refresh=refresh, simulations=simulations)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/override_match")
async def override_match_endpoint(request: OverrideMatchRequest):
    try:
        return {"message": "Tournament recalculated from overridden match.", "data": override_match(
            request.match_id,
            request.home_score,
            request.away_score,
            request.penalties_winner,
        )}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/resimulate")
async def resimulate_endpoint(request: ResimulateRequest):
    try:
        return {"message": "Tournament recalculated from overridden match.", "data": resimulate_from_match(request.match_id)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/play_as")
async def play_as_endpoint(request: PlayAsRequest):
    try:
        return {"message": f"Play-as simulation completed for {request.team_name}.", "data": play_as_team(request.team_name, simulations=request.simulations, seed=request.seed)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
