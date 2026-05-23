"""Team-level momentum and live match-state engine."""

from __future__ import annotations

import random
from typing import Any, Dict, List

from match_engine.utils.helpers import clamp


class MatchMomentumEngine:
    """Build live match states and momentum traces for timeline simulation."""

    def build_match_states(
        self,
        *,
        home_state: Dict[str, Any],
        away_state: Dict[str, Any],
        home_tactical: Dict[str, Any],
        away_tactical: Dict[str, Any],
        stage: str,
        extra_time: bool,
        penalties: bool,
        rng: random.Random,
    ) -> List[Dict[str, Any]]:
        minutes = [0, 15, 30, 45, 60, 75, 90]
        if extra_time:
            minutes.append(105)
        if penalties:
            minutes.append(120)

        pressure_stage = {"R32": 3.0, "R16": 4.5, "QF": 6.0, "SF": 7.5, "FINAL": 8.0}.get(stage, 2.0)

        traces: List[Dict[str, Any]] = []
        for minute in minutes:
            fatigue_weight = 1.0 + (minute / 120.0)

            home_pressure = self._metric(
                base=52.0,
                tactical=float(home_state.get("tactical_intensity", 1.0)),
                morale=float(home_state.get("morale", 1.0)),
                confidence=float(home_state.get("confidence", 1.0)),
                fatigue=float(home_state.get("fatigue", 0.0)) * fatigue_weight,
                noise=rng.uniform(-4.0, 4.0),
            )
            away_pressure = self._metric(
                base=52.0,
                tactical=float(away_state.get("tactical_intensity", 1.0)),
                morale=float(away_state.get("morale", 1.0)),
                confidence=float(away_state.get("confidence", 1.0)),
                fatigue=float(away_state.get("fatigue", 0.0)) * fatigue_weight,
                noise=rng.uniform(-4.0, 4.0),
            )

            home_compact = self._compactness(home_state, pressure_stage, rng)
            away_compact = self._compactness(away_state, pressure_stage, rng)

            home_possession = self._possession(home_tactical, home_pressure, away_pressure, rng)
            away_possession = round(100.0 - home_possession, 1)

            home_counter = self._counter_intensity(home_tactical, away_possession, rng)
            away_counter = self._counter_intensity(away_tactical, home_possession, rng)

            home_aggression = self._aggression(home_state, pressure_stage, rng)
            away_aggression = self._aggression(away_state, pressure_stage, rng)

            traces.append(
                {
                    "minute": self._minute_label(minute),
                    "home": {
                        "attacking_pressure": home_pressure,
                        "defensive_compactness": home_compact,
                        "possession_control": home_possession,
                        "counterattacking_intensity": home_counter,
                        "tactical_aggression": home_aggression,
                    },
                    "away": {
                        "attacking_pressure": away_pressure,
                        "defensive_compactness": away_compact,
                        "possession_control": away_possession,
                        "counterattacking_intensity": away_counter,
                        "tactical_aggression": away_aggression,
                    },
                }
            )

        return traces

    def build_possession_trace(self, match_states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        trace: List[Dict[str, Any]] = []
        for state in match_states:
            minute = state.get("minute")
            home = float(state.get("home", {}).get("possession_control", 50.0))
            away = float(state.get("away", {}).get("possession_control", 50.0))
            adjusted_home = max(30.0, min(70.0, round(home, 1)))
            adjusted_away = round(100.0 - adjusted_home, 1)
            trace.append({"minute": minute, "home": adjusted_home, "away": adjusted_away})
        return trace

    def build_momentum_trace(
        self,
        *,
        match_states: List[Dict[str, Any]],
        timeline: List[Dict[str, Any]],
        home_team: str,
        away_team: str,
    ) -> List[Dict[str, Any]]:
        event_boost = {}
        for event in timeline:
            minute = str(event.get("minute"))
            event_type = str(event.get("event_type"))
            team = str(event.get("team"))
            if team not in {home_team, away_team}:
                continue
            swing = 0.0
            if event_type in {"Goal", "Penalty Goal", "Late Winner", "Injury Time Goal"}:
                swing = 8.5
            elif event_type == "Equalizer":
                swing = 6.0
            elif event_type in {"Momentum Shift", "Tactical Pressure", "Possession Domination"}:
                swing = 4.5
            elif event_type == "Red Card":
                swing = 7.0
            elif event_type == "Defensive Collapse":
                swing = 5.0
            if swing == 0.0:
                continue
            signed = swing if team == home_team else -swing
            event_boost[minute] = event_boost.get(minute, 0.0) + signed

        trace: List[Dict[str, Any]] = []
        baseline = 50.0
        for state in match_states:
            minute = str(state.get("minute"))
            home = state.get("home", {})
            away = state.get("away", {})
            pressure_gap = float(home.get("attacking_pressure", 50.0)) - float(away.get("attacking_pressure", 50.0))
            possession_gap = float(home.get("possession_control", 50.0)) - float(away.get("possession_control", 50.0))
            compact_gap = float(home.get("defensive_compactness", 50.0)) - float(away.get("defensive_compactness", 50.0))
            value = baseline + pressure_gap * 0.55 + possession_gap * 0.38 + compact_gap * 0.22 + event_boost.get(minute, 0.0)
            value = max(10.0, min(90.0, round(value, 1)))
            trace.append({"minute": minute, "home": value, "away": round(100.0 - value, 1)})
        return trace

    def build_xg_progression(self, home_xg: float, away_xg: float, match_states: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not match_states:
            return []
        total_steps = len(match_states)
        progression: List[Dict[str, Any]] = []
        cumulative_home = 0.0
        cumulative_away = 0.0
        for idx, state in enumerate(match_states, 1):
            minute = str(state.get("minute"))
            home_pressure = float(state.get("home", {}).get("attacking_pressure", 50.0))
            away_pressure = float(state.get("away", {}).get("attacking_pressure", 50.0))
            step_base_home = home_xg / total_steps
            step_base_away = away_xg / total_steps
            step_home = step_base_home * (0.88 + (home_pressure / 100.0) * 0.24)
            step_away = step_base_away * (0.88 + (away_pressure / 100.0) * 0.24)
            cumulative_home += step_home
            cumulative_away += step_away
            if idx == total_steps:
                cumulative_home = home_xg
                cumulative_away = away_xg
            progression.append({"minute": minute, "home": round(cumulative_home, 2), "away": round(cumulative_away, 2)})
        return progression

    def summarize_match_momentum(self, timeline: List[Dict[str, Any]], momentum_trace: List[Dict[str, Any]]) -> str:
        if not timeline or not momentum_trace:
            return "Momentum remained balanced with limited decisive swings."

        pressure_events = sum(1 for event in timeline if event.get("event_type") in {"Tactical Pressure", "Possession Domination"})
        swing_events = sum(1 for event in timeline if event.get("event_type") == "Momentum Shift")
        late_drama = any(str(event.get("minute", "")).startswith("90+") or event.get("event_type") in {"Late Winner", "Injury Time Goal"} for event in timeline)
        final_home = float(momentum_trace[-1].get("home", 50.0))
        edge = "home side" if final_home > 54 else "away side" if final_home < 46 else "neither side"

        summary = f"{swing_events} momentum swings and {pressure_events} sustained pressure spells shaped the match; the {edge} held the late control edge."
        if late_drama:
            summary += " The closing phase produced high-pressure late drama."
        return summary

    def _metric(self, *, base: float, tactical: float, morale: float, confidence: float, fatigue: float, noise: float) -> float:
        value = base
        value += (tactical - 1.0) * 22.0
        value += (morale - 1.0) * 14.0
        value += (confidence - 1.0) * 12.0
        value -= fatigue * 28.0
        value += noise
        return round(clamp(value, 22.0, 88.0), 1)

    def _compactness(self, state: Dict[str, Any], pressure_stage: float, rng: random.Random) -> float:
        compactness = 50.0
        compactness += (float(state.get("defensive_compactness", 1.0)) - 1.0) * 18.0
        compactness += (float(state.get("pressure_resilience", 1.0)) - 1.0) * 12.0
        compactness += pressure_stage * 0.7
        compactness -= float(state.get("fatigue", 0.0)) * 18.0
        compactness += rng.uniform(-3.0, 3.0)
        return round(clamp(compactness, 24.0, 86.0), 1)

    def _possession(self, tactical: Dict[str, Any], own_pressure: float, opp_pressure: float, rng: random.Random) -> float:
        style = str(tactical.get("style", "balanced"))
        style_bias = {
            "possession": 6.5,
            "balanced_attack": 3.0,
            "attacking": 1.0,
            "pressing": 2.0,
            "balanced": 0.0,
            "structured": -1.5,
            "gritty": -2.0,
            "defensive": -4.0,
        }.get(style, 0.0)
        base = 50.0 + style_bias + (own_pressure - opp_pressure) * 0.28 + rng.uniform(-2.5, 2.5)
        return round(clamp(base, 31.0, 69.0), 1)

    def _counter_intensity(self, tactical: Dict[str, Any], opponent_possession: float, rng: random.Random) -> float:
        style = str(tactical.get("style", "balanced"))
        style_bias = {
            "defensive": 8.0,
            "structured": 6.0,
            "gritty": 6.5,
            "balanced": 4.0,
            "attacking": 2.5,
            "balanced_attack": 3.0,
            "possession": 1.5,
            "pressing": 2.0,
        }.get(style, 4.0)
        base = 32.0 + style_bias + (opponent_possession - 50.0) * 0.35 + rng.uniform(-3.0, 3.0)
        return round(clamp(base, 18.0, 84.0), 1)

    def _aggression(self, state: Dict[str, Any], pressure_stage: float, rng: random.Random) -> float:
        base = 46.0
        base += (float(state.get("tactical_intensity", 1.0)) - 1.0) * 24.0
        base += pressure_stage
        base += rng.uniform(-3.0, 3.0)
        return round(clamp(base, 24.0, 86.0), 1)

    @staticmethod
    def _minute_label(minute: int) -> str:
        if minute in {105, 120}:
            return f"{minute}'"
        if minute > 90:
            return f"90+{minute - 90}'"
        return f"{minute}'"
