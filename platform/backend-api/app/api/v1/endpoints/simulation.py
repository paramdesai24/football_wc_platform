from fastapi import APIRouter
from pydantic import BaseModel
from pydantic import Field
import sys
import pandas as pd
from pathlib import Path
import os

# Add tournament engine to path - use absolute path resolution
current_file = Path(__file__).resolve()
backend_api_dir = current_file.parents[3]  # backend-api
platform_dir = backend_api_dir.parent  # platform
project_root = platform_dir.parent  # FIFA WC

# Add both to path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "tournament_engine"))

router = APIRouter()


class SimulationRequest(BaseModel):
    iterations: int = 200
    model: str = "hybrid"
    fixed_results: dict = Field(default_factory=dict)


def load_rankings():
    try:
        p = Path(r"C:\FIFA WC\platform\data\processed\dynamic_world_rankings_active.csv")
        return pd.read_csv(p)
    except Exception as e:
        print(f"Error loading rankings: {e}")
        return pd.DataFrame()


def get_tournament_engine():
    """Lazy load tournament engine on first use."""
    import importlib.util
    from pathlib import Path
    import sys
    
    # Determine paths - file is at: c:\FIFA WC\platform\backend-api\app\api\v1\endpoints\simulation.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parents[6]  # Go up to FIFA WC root
    
    try:
        print(f"[SIMULATION] Project root: {project_root}")
        
        # Try standard import first
        try:
            if str(project_root) not in sys.path:
                sys.path.insert(0, str(project_root))
            from tournament_engine.simulation.monte_carlo import MonteCarloTournament
            from match_engine.probabilities.match_probability import MatchProbabilityEngine
            print(f"[SIMULATION] SUCCESS Standard import successful")
            return MonteCarloTournament, MatchProbabilityEngine, None
        except ModuleNotFoundError:
            print(f"[SIMULATION] Standard import failed, trying importlib...")
            pass
        
        # Fallback: use importlib to load directly from file
        monte_carlo_path = project_root / "tournament_engine" / "simulation" / "monte_carlo.py"
        engine_path = project_root / "match_engine" / "probabilities" / "match_probability.py"
        
        if not monte_carlo_path.exists():
            raise FileNotFoundError(f"Monte Carlo module not found at {monte_carlo_path}")
        if not engine_path.exists():
            raise FileNotFoundError(f"Engine module not found at {engine_path}")
        
        # Load probability engine first
        spec = importlib.util.spec_from_file_location("match_probability", engine_path)
        prob_module = importlib.util.module_from_spec(spec)
        sys.modules["match_probability"] = prob_module
        spec.loader.exec_module(prob_module)
        
        # Load Monte Carlo
        spec = importlib.util.spec_from_file_location("monte_carlo_sim", monte_carlo_path)
        mc_module = importlib.util.module_from_spec(spec)
        sys.modules["monte_carlo_sim"] = mc_module
        spec.loader.exec_module(mc_module)
        
        MonteCarloTournament = mc_module.MonteCarloTournament
        MatchProbabilityEngine = prob_module.MatchProbabilityEngine
        
        print(f"[SIMULATION] SUCCESS Importlib load successful")
        return MonteCarloTournament, MatchProbabilityEngine, None
        
    except Exception as e:
        print(f"[SIMULATION] Import error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return None, None, str(e)


@router.post("/run")
async def run_simulation(request: SimulationRequest):
    """Run Monte Carlo tournament simulation with proper group stages and knockouts."""
    
    MonteCarloTournament, MatchProbabilityEngine, import_error = get_tournament_engine()
    
    if MonteCarloTournament is None:
        return {
            "error": f"Tournament simulation engine not available: {import_error}",
            "iterations": 0,
            "results": [],
            "total_teams": 0
        }
    
    try:
        # Limit iterations to reasonable max
        n_iterations = min(max(request.iterations, 10), 500)
        
        print(f"[SIMULATION] Starting {n_iterations} tournament simulations...")
        
        # Run proper tournament simulation
        prediction_engine = MatchProbabilityEngine()
        mc = MonteCarloTournament(
            n_simulations=n_iterations,
            prediction_engine=prediction_engine,
            fixed_results=request.fixed_results or {},
        )
        probs_dict = mc.run()
        
        print(f"[SIMULATION] Completed simulations, extracting results...")
        
        # Extract champion probabilities
        results = []
        for rank, (team, prob) in enumerate(mc.get_top_champions(n=32), 1):
            results.append({
                "rank": rank,
                "team": team,
                "country_name": team,
                "win_pct": round(prob * 100, 1),
                "wins": int(prob * n_iterations),
            })

        statistics = mc.get_aggregate_statistics()
        
        print(f"[SIMULATION] Returning {len(results[:10])} top champions")
        
        return {
            "iterations": n_iterations,
            "results": results[:10],  # Top 10
            "total_teams": len(results),
            "statistics": statistics,
            "note": "Full tournament simulation (groups → knockouts)"
        }
        
    except Exception as e:
        print(f"[SIMULATION] Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": f"Simulation failed: {str(e)}",
            "iterations": 0,
            "results": [],
            "total_teams": 0,
            "statistics": {},
        }


@router.get("/results")
async def simulation_results():
    return {"data": [], "total": 0}


@router.get("/latest")
async def latest_simulation():
    df = load_rankings()
    if df.empty:
        return {"data": None}
    
    top_5 = df.head(5)
    return {
        "data": top_5[["country_name", "elo_rating"]].to_dict("records"),
        "iterations": 100,
    }
