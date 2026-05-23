from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from tournament_engine.analysis.advanced_match_intelligence import AdvancedMatchIntelligenceEngine
from tournament_engine.simulation.tournament import TournamentSimulator

from .state_store import load_json, save_json, sanitize_jsonable


BACKEND_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
STATE_FILE = BACKEND_DATA_DIR / "tournament_state.json"
PLAY_AS_HISTORY_FILE = BACKEND_DATA_DIR / "play_as_history.json"

_INTELLIGENCE = AdvancedMatchIntelligenceEngine(seed=2026)

STAGE_ORDER = ["GROUP", "R32", "R16", "QF", "SF", "THIRD_PLACE", "FINAL"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_state() -> Dict[str, Any]:
    return load_json(STATE_FILE, {})


def _save_state(state: Dict[str, Any]) -> None:
    save_json(STATE_FILE, state)


def _normalize_stage(stage: str) -> str:
    mapping = {
        "group": "GROUP", "GS": "GROUP",
        "R32": "R32", "R16": "R16", "QF": "QF", "SF": "SF",
        "3rd_place": "THIRD_PLACE", "Third Place": "THIRD_PLACE",
        "Final": "FINAL", "FINAL": "FINAL",
    }
    return mapping.get(stage, stage.upper())


def _stage_sort_key(match: Dict[str, Any]) -> tuple:
    stage = _normalize_stage(str(match.get("stage", "")))
    stage_idx = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else len(STAGE_ORDER)
    mid = match.get("match_id", 0)
    if isinstance(mid, int):
        return stage_idx, mid
    digits = "".join(ch for ch in str(mid) if ch.isdigit())
    return stage_idx, int(digits) if digits else 0


def _build_match_record(result: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a raw simulation result into a normalized match record."""
    stage = _normalize_stage(result.get("stage", ""))
    return {
        "match_id": result.get("match_id"),
        "stage": stage,
        "group": result.get("group"),
        "matchday": result.get("matchday"),
        "home_team": result.get("home_team", "TBD"),
        "away_team": result.get("away_team", "TBD"),
        "home_goals": result.get("home_goals"),
        "away_goals": result.get("away_goals"),
        "home_score": result.get("home_goals"),
        "away_score": result.get("away_goals"),
        "winner": result.get("winner"),
        "loser": result.get("loser"),
        "penalties": bool(result.get("penalties", False)),
        "penalty_score": result.get("penalty_score"),
        "extra_time": bool(result.get("extra_time", False)),
        "editable": stage != "FINAL",
        "locked": stage == "FINAL",
        "user_overridden": bool(result.get("user_overridden", False)),
        "home_win_prob": result.get("home_win_prob"),
        "away_win_prob": result.get("away_win_prob"),
        "draw_prob": result.get("draw_prob"),
        "home_xg": result.get("home_xg"),
        "away_xg": result.get("away_xg"),
        "result_type": result.get("result_type"),
    }


def _build_matches_from_raw(raw_state: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Build a flat matches list from raw group_results + knockout_results."""
    matches = [_build_match_record(r) for r in raw_state.get("group_results", [])]
    matches.extend(_build_match_record(r) for r in raw_state.get("knockout_results", []))
    matches.sort(key=_stage_sort_key)
    return matches


def _enrich_state(raw_state: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich raw tournament state with timelines, momentum, and analyst data."""
    enriched = dict(raw_state)
    team_state = enriched.get("team_state", {}) or {}

    # Build matches from raw results if not already present
    if not enriched.get("matches"):
        enriched["matches"] = _build_matches_from_raw(raw_state)

    # Enrich each match with timeline and intelligence
    enriched["matches"] = [
        _INTELLIGENCE.enrich_match(match, team_state)
        for match in enriched["matches"]
    ]
    enriched["updated_at"] = _utc_now()
    return sanitize_jsonable(enriched)


def _run_simulation_with_fixed_results(
    fixed_results: Dict[Any, Dict[str, Any]],
    seed: int = 2026,
    num_simulations: int = 10,
) -> Dict[str, Any]:
    sim_final = TournamentSimulator(seed=seed, stochastic=True, fixed_results=fixed_results)
    sim_final.run()
    state = _enrich_state(sim_final.get_tournament_state())
    _save_state(state)
    return state


def get_tournament_results(refresh: bool = False) -> Dict[str, Any]:
    state = _load_state()
    if refresh or not state.get("matches"):
        state = _run_simulation_with_fixed_results(
            {}, seed=int(state.get("seed", 2026) or 2026), num_simulations=100,
        )
    elif state.get("matches") and not state.get("matches", [{}])[0].get("timeline"):
        state = _enrich_state(state)
        _save_state(state)
    return sanitize_jsonable(state)


def play_as_team(team_name: str, simulations: int = 10, seed: int = 2026) -> Dict[str, Any]:
    """Run N tournament simulations and extract the chosen team's journey from each."""
    journeys: List[Dict[str, Any]] = []
    for index in range(simulations):
        sim = TournamentSimulator(seed=seed + index, stochastic=True)
        sim.run()
        state = _enrich_state(sim.get_tournament_state())
        journey = _INTELLIGENCE.build_team_journey(team_name, state)
        journey["simulation"] = index + 1
        journeys.append(journey)

    summary = _INTELLIGENCE.summarize_play_as(team_name, journeys)
    payload = {
        "team": team_name,
        "simulations": simulations,
        "summary": summary,
        "journeys": journeys,
        "generated_at": _utc_now(),
    }

    history = load_json(PLAY_AS_HISTORY_FILE, [])
    history.append(payload)
    history = history[-25:]
    save_json(PLAY_AS_HISTORY_FILE, history)
    return sanitize_jsonable(payload)
