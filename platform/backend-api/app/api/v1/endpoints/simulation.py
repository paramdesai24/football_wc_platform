from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class SimulationRequest(BaseModel):
    iterations: int = 10000
    model: str = "hybrid"


@router.post("/run")
async def run_simulation(request: SimulationRequest):
    return {
        "data": None,
        "message": f"Monte Carlo simulation ({request.iterations} iterations) pending engine integration",
        "request": request.model_dump(),
    }


@router.get("/results")
async def simulation_results():
    return {"data": [], "total": 0}


@router.get("/latest")
async def latest_simulation():
    return {"data": None, "message": "No simulations run yet"}
