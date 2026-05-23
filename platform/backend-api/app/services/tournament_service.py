from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from collections import defaultdict, Counter
import logging
import sys
import random

PROJECT_ROOT = Path(__file__).resolve().parents[4]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tournament_engine.knockouts.bracket import R16_MATCHES, QF_MATCHES, SF_MATCHES
from tournament_engine.simulation.tournament import TournamentSimulator
from tournament_engine.analysis.advanced_match_intelligence import AdvancedMatchIntelligenceEngine

from .state_store import load_json, save_json, sanitize_jsonable

logger = logging.getLogger(__name__)

# Monte Carlo simulation defaults
# Full/accurate run (used for background or explicit full runs)
FULL_RUN_SIMULATIONS = 100
# Quick runs intended for UI refreshes / quick overrides to keep latency low
UI_REFRESH_SIMULATIONS = 2
QUICK_OVERRIDE_SIMULATIONS = 3


BACKEND_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
STATE_FILE = BACKEND_DATA_DIR / "tournament_state.json"

_INTELLIGENCE = AdvancedMatchIntelligenceEngine(seed=2026)

STAGE_ORDER = ["GROUP", "R32", "R16", "QF", "SF", "THIRD_PLACE", "FINAL"]
STAGE_DOWNSTREAM = {
    "GROUP": ["R32", "R16", "QF", "SF", "THIRD_PLACE", "FINAL"],
    "R32": ["R16", "QF", "SF", "THIRD_PLACE", "FINAL"],
    "R16": ["QF", "SF", "THIRD_PLACE", "FINAL"],
    "QF": ["SF", "THIRD_PLACE", "FINAL"],
    "SF": ["THIRD_PLACE", "FINAL"],
    "THIRD_PLACE": [],
    "FINAL": [],
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_stage(stage: str) -> str:
    mapping = {
        "group": "GROUP",
        "GS": "GROUP",
        "R32": "R32",
        "R16": "R16",
        "QF": "QF",
        "SF": "SF",
        "3rd_place": "THIRD_PLACE",
        "Third Place": "THIRD_PLACE",
        "Final": "FINAL",
        "FINAL": "FINAL",
    }
    return mapping.get(stage, stage.upper())


def _stage_sort_key(match: Dict[str, Any]) -> tuple:
    stage = _normalize_stage(match.get("stage", ""))
    stage_index = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else len(STAGE_ORDER)
    match_id = match.get("match_id", "")
    if isinstance(match_id, int):
        match_sort = match_id
    else:
        digits = "".join(ch for ch in str(match_id) if ch.isdigit())
        match_sort = int(digits) if digits else str(match_id)
    return stage_index, match_sort


def _dependency_map(match_id: Any, stage: str) -> List[Any]:
    normalized = _normalize_stage(stage)
    if normalized == "R16":
        info = R16_MATCHES.get(int(match_id), {})
        return [info.get("home_from"), info.get("away_from")]
    if normalized == "QF":
        info = QF_MATCHES.get(int(match_id), {})
        return [info.get("home_from"), info.get("away_from")]
    if normalized == "SF":
        info = SF_MATCHES.get(int(match_id), {})
        return [info.get("home_from"), info.get("away_from")]
    if normalized in {"THIRD_PLACE", "FINAL"}:
        return [101, 102]
    return []


def _build_match_record(result: Dict[str, Any]) -> Dict[str, Any]:
    stage = _normalize_stage(result.get("stage", ""))
    match_id = result.get("match_id")
    dependencies = _dependency_map(match_id, result.get("stage", ""))

    penalties = bool(result.get("penalties", False))
    extra_time = bool(result.get("extra_time", False))
    editable = stage != "FINAL"

    return {
        "match_id": match_id,
        "stage": stage,
        "group": result.get("group"),
        "matchday": result.get("matchday"),
        "home_team": result.get("home_team", "TBD"),
        "away_team": result.get("away_team", "TBD"),
        "home_score": result.get("home_goals"),
        "away_score": result.get("away_goals"),
        "winner": result.get("winner"),
        "loser": result.get("loser"),
        "penalties": penalties,
        "penalty_score": result.get("penalty_score"),
        "extra_time": extra_time,
        "editable": editable,
        "locked": not editable,
        "dependencies": [dep for dep in dependencies if dep not in (None, "")],
        "user_overridden": bool(result.get("user_overridden", False)),
        "home_win_prob": result.get("home_win_prob"),
        "away_win_prob": result.get("away_win_prob"),
        "draw_prob": result.get("draw_prob"),
        "home_xg": result.get("home_xg"),
        "away_xg": result.get("away_xg"),
        "result_type": result.get("result_type"),
    }


def _build_state(sim: TournamentSimulator) -> Dict[str, Any]:
    raw_state = sim.get_tournament_state()
    matches = [_build_match_record(result) for result in raw_state.get("group_results", [])]
    matches.extend(_build_match_record(result) for result in raw_state.get("knockout_results", []))
    matches.sort(key=_stage_sort_key)

    enriched_matches = [_INTELLIGENCE.enrich_match(match, raw_state.get("team_state", {})) for match in matches]

    return sanitize_jsonable({
        **raw_state,
        "matches": enriched_matches,
        "updated_at": _utc_now(),
    })


def _fixed_results_for_stage(state: Dict[str, Any], target_match_id: Any) -> Dict[Any, Dict[str, Any]]:
    matches = state.get("matches", [])
    target = next((match for match in matches if match.get("match_id") == target_match_id), None)
    if not target:
        return {}

    target_stage = _normalize_stage(target.get("stage", ""))
    downstream_stages = set(STAGE_DOWNSTREAM.get(target_stage, []))

    fixed_results: Dict[Any, Dict[str, Any]] = {}
    for match in matches:
        stage = _normalize_stage(match.get("stage", ""))
        if stage in downstream_stages:
            continue
        fixed_results[match.get("match_id")] = _match_to_sim_result(match)
    return fixed_results


def _match_to_sim_result(match: Dict[str, Any]) -> Dict[str, Any]:
    stage = match.get("stage", "")
    if stage == "THIRD_PLACE":
        stage = "3rd_place"
    elif stage == "FINAL":
        stage = "Final"
    elif stage == "GROUP":
        stage = "group"
    return {
        "match_id": match.get("match_id"),
        "stage": stage,
        "group": match.get("group"),
        "matchday": match.get("matchday"),
        "home_team": match.get("home_team", "TBD"),
        "away_team": match.get("away_team", "TBD"),
        "home_goals": match.get("home_score"),
        "away_goals": match.get("away_score"),
        "winner": match.get("winner"),
        "loser": match.get("loser"),
        "penalties": bool(match.get("penalties", False)),
        "penalty_score": match.get("penalty_score"),
        "extra_time": bool(match.get("extra_time", False)),
        "user_overridden": bool(match.get("user_overridden", False)),
        "home_win_prob": match.get("home_win_prob"),
        "away_win_prob": match.get("away_win_prob"),
        "draw_prob": match.get("draw_prob"),
        "home_xg": match.get("home_xg"),
        "away_xg": match.get("away_xg"),
        "result_type": match.get("result_type"),
    }


def _load_state() -> Dict[str, Any]:
    return load_json(STATE_FILE, {})


def _save_state(state: Dict[str, Any]) -> None:
    save_json(STATE_FILE, state)


def build_override_payload(match: Dict[str, Any], home_score: int, away_score: int, penalties_winner: Optional[str]) -> Dict[str, Any]:
    stage = _normalize_stage(match.get("stage", ""))
    is_knockout = stage != "GROUP"
    penalties = False
    extra_time = False
    penalty_score = None
    winner = None
    loser = None

    if is_knockout:
        if home_score == away_score:
            if penalties_winner not in {"home", "away"}:
                raise ValueError("Knockout matches cannot end in a draw without a penalties winner.")
            penalties = True
            extra_time = True
            penalty_score = "5-4" if penalties_winner == "home" else "4-5"
            winner = match.get("home_team") if penalties_winner == "home" else match.get("away_team")
            loser = match.get("away_team") if penalties_winner == "home" else match.get("home_team")
        else:
            winner = match.get("home_team") if home_score > away_score else match.get("away_team")
            loser = match.get("away_team") if home_score > away_score else match.get("home_team")
    else:
        if home_score > away_score:
            winner = match.get("home_team")
            loser = match.get("away_team")
        elif away_score > home_score:
            winner = match.get("away_team")
            loser = match.get("home_team")

    return {
        "match_id": match.get("match_id"),
        "stage": match.get("stage"),
        "group": match.get("group"),
        "matchday": match.get("matchday"),
        "home_team": match.get("home_team"),
        "away_team": match.get("away_team"),
        "home_goals": home_score,
        "away_goals": away_score,
        "winner": winner,
        "loser": loser,
        "extra_time": extra_time,
        "penalties": penalties,
        "penalty_score": penalty_score,
        "home_win_prob": match.get("home_win_prob"),
        "away_win_prob": match.get("away_win_prob"),
        "draw_prob": match.get("draw_prob"),
        "home_xg": match.get("home_xg"),
        "away_xg": match.get("away_xg"),
        "result_type": "penalties" if penalties else "extra_time" if extra_time else "regulation",
        "user_overridden": True,
    }


def _run_simulation_with_fixed_results(fixed_results: Dict[Any, Dict[str, Any]], seed: int = 2026, num_simulations: int = 10) -> Dict[str, Any]:
    """
    Run num_simulations tournament simulations with aggregated probabilities.
    Each simulation uses a different seed for stochastic variation.
    
    Args:
        fixed_results: Dict of match IDs with locked results
        seed: Base random seed
        num_simulations: Number of MC simulations to run (default 10 for overrides, 100 for full runs)
    """
    logger.info(f"Running {num_simulations} Monte Carlo tournament simulations with seed={seed}...")
    
    # Track all match outcomes across simulations AND keep raw states
    match_outcomes: Dict[Any, List[Dict[str, Any]]] = defaultdict(list)
    standings_by_sim = []
    sim_states = []  # Keep all simulation states
    
    # Run multiple simulations with varied seeds
    for i in range(num_simulations):
        sim_seed = seed + i
        sim = TournamentSimulator(seed=sim_seed, stochastic=True, fixed_results=fixed_results)
        sim.run()
        raw_state = sim.get_tournament_state()
        standings_by_sim.append(raw_state.get("standings", {}))
        sim_states.append((i, raw_state))  # Store sim index and state
        
        # Collect all match outcomes
        for result in raw_state.get("group_results", []) + raw_state.get("knockout_results", []):
            match_id = result.get("match_id")
            match_outcomes[match_id].append(result)
    
    logger.info(f"Completed {num_simulations} simulations, aggregating results...")
    
    # Aggregate match results and compute probabilities
    aggregated_matches = []
    for match_id, outcomes in match_outcomes.items():
        # Use first outcome as template
        primary = outcomes[0]
        
        # Calculate outcome frequencies
        home_wins = sum(1 for o in outcomes if o.get("winner") == o.get("home_team"))
        away_wins = sum(1 for o in outcomes if o.get("winner") == o.get("away_team"))
        draws = sum(1 for o in outcomes if o.get("winner") is None or o.get("draw"))
        
        # Most likely outcome (from first sim or most frequent)
        most_frequent = Counter([tuple(sorted([
            o.get("home_goals", 0),
            o.get("away_goals", 0)
        ])) for o in outcomes]).most_common(1)
        
        match_result = {
            **primary,
            # Override with most frequent outcome
            "home_goals": most_frequent[0][0][0] if most_frequent else primary.get("home_goals"),
            "away_goals": most_frequent[0][0][1] if most_frequent else primary.get("away_goals"),
            # Computed probabilities from MC runs
            "home_win_prob": home_wins / num_simulations,
            "away_win_prob": away_wins / num_simulations,
            "draw_prob": draws / num_simulations,
            "simulations_run": num_simulations,
        }
        aggregated_matches.append(match_result)
    
    # Select one of the actual simulations as the base state
    # Use deterministic selection based on seed to ensure different seeds produce different results
    # seed=123456 picks sim 6, seed=654321 picks sim 1, etc.
    random_choice = seed % num_simulations
    selected_sim_index, selected_raw_state = sim_states[random_choice]
    logger.info(f"Seed {seed} selected simulation {selected_sim_index} ({seed} % {num_simulations} = {random_choice})")
    
    # Build matches from the selected simulation's raw results
    matches = [_build_match_record(result) for result in selected_raw_state.get("group_results", [])]
    matches.extend(_build_match_record(result) for result in selected_raw_state.get("knockout_results", []))
    matches.sort(key=_stage_sort_key)
    
    # Enrich matches with analysis
    enriched_matches = [_INTELLIGENCE.enrich_match(match, selected_raw_state.get("team_state", {})) for match in matches]
    
    # Create state from the selected simulation
    state = sanitize_jsonable({
        **selected_raw_state,
        "matches": enriched_matches,
        "updated_at": _utc_now(),
    })
    
    # Update state with aggregated probabilities
    for i, match_record in enumerate(state.get("matches", [])):
        for agg in aggregated_matches:
            if match_record.get("match_id") == agg.get("match_id"):
                match_record["home_win_prob"] = agg["home_win_prob"]
                match_record["away_win_prob"] = agg["away_win_prob"]
                match_record["draw_prob"] = agg["draw_prob"]
                match_record["mc_simulations"] = num_simulations
                break
    
    _save_state(state)
    return state


def get_tournament_results(refresh: bool = False, simulations: Optional[int] = None) -> Dict[str, Any]:
    state = _load_state()
    if refresh or not state.get("matches"):
        # Generate new seed for different results on each refresh
        new_seed = random.randint(1, 1000000) if refresh else int(state.get("seed", 2026) or 2026)
        logger.info(f"Tournament refresh={refresh}, generated seed={new_seed}, simulations={simulations}")
        # Determine simulation count: explicit request wins, otherwise use quick UI defaults
        num_simulations = int(simulations) if simulations is not None else UI_REFRESH_SIMULATIONS
        state = _run_simulation_with_fixed_results({}, seed=new_seed, num_simulations=num_simulations)
        # Update seed in state so it's preserved for non-refresh loads
        state["seed"] = new_seed
    return sanitize_jsonable(state)


def override_match(match_id: Any, home_score: int, away_score: int, penalties_winner: Optional[str] = None) -> Dict[str, Any]:
    state = get_tournament_results(refresh=False)
    matches = state.get("matches", [])
    match = next((item for item in matches if item.get("match_id") == match_id), None)
    if not match:
        raise ValueError(f"Match {match_id} not found")
    if not match.get("editable", True):
        raise ValueError("The final match is locked and cannot be edited.")

    if home_score < 0 or away_score < 0:
        raise ValueError("Scores must be non-negative integers.")

    payload = build_override_payload(match, home_score, away_score, penalties_winner)
    current_by_id = {item.get("match_id"): item for item in matches}
    current_by_id[match_id] = {**match, **payload, "user_overridden": True}

    fixed_results = {}
    for item in matches:
        stage = _normalize_stage(item.get("stage", ""))
        target_stage = _normalize_stage(match.get("stage", ""))
        if STAGE_ORDER.index(stage) > STAGE_ORDER.index(target_stage):
            continue
        if stage in STAGE_DOWNSTREAM.get(target_stage, []):
            continue
        source = current_by_id.get(item.get("match_id"), item)
        fixed_results[item.get("match_id")] = _match_to_sim_result(source)

    fixed_results[match_id] = payload
    # Run override with a few simulations for quick feedback
    new_state = _run_simulation_with_fixed_results(fixed_results, seed=int(state.get("seed", 2026) or 2026), num_simulations=QUICK_OVERRIDE_SIMULATIONS)
    new_state["last_override"] = {
        "match_id": match_id,
        "timestamp": _utc_now(),
    }
    _save_state(new_state)
    return sanitize_jsonable(new_state)


def resimulate_from_match(match_id: Any) -> Dict[str, Any]:
    state = get_tournament_results(refresh=False)
    matches = state.get("matches", [])
    match = next((item for item in matches if item.get("match_id") == match_id), None)
    if not match:
        raise ValueError(f"Match {match_id} not found")

    target_stage = _normalize_stage(match.get("stage", ""))
    fixed_results = {}
    for item in matches:
        stage = _normalize_stage(item.get("stage", ""))
        if stage in STAGE_DOWNSTREAM.get(target_stage, []):
            continue
        fixed_results[item.get("match_id")] = _match_to_sim_result(item)

    # Run resimulation with a few simulations for quick feedback
    new_state = _run_simulation_with_fixed_results(fixed_results, seed=int(state.get("seed", 2026) or 2026), num_simulations=QUICK_OVERRIDE_SIMULATIONS)
    new_state["last_resimulated_from"] = {
        "match_id": match_id,
        "timestamp": _utc_now(),
    }
    _save_state(new_state)
    return sanitize_jsonable(new_state)
