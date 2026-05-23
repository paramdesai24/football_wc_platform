"""Team-level match intelligence, timeline, and play-as summaries.

This module deliberately stays at the team level. It does not fabricate
player events, player ratings, or any player-specific match objects.
"""

from __future__ import annotations

import random
from collections import Counter
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from match_engine.utils.constants import TACTICAL_PROFILES, DEFAULT_TACTICAL_PROFILE
from .timeline_engine import LiveTimelineEngine
from .momentum_engine import MatchMomentumEngine
from .play_as_mode import PlayAsTeamMode


STAGE_ORDER = ["GROUP", "R32", "R16", "QF", "SF", "THIRD_PLACE", "FINAL"]


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


def _stage_label(stage: str) -> str:
    return {
        "GROUP": "Group Stage",
        "R32": "Round of 32",
        "R16": "Round of 16",
        "QF": "Quarter-Final",
        "SF": "Semi-Final",
        "THIRD_PLACE": "Third-Place Playoff",
        "FINAL": "Final",
    }.get(stage, stage)


def _match_sort_key(match: Dict[str, Any]) -> tuple:
    stage = _normalize_stage(str(match.get("stage", "")))
    stage_index = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else len(STAGE_ORDER)
    match_id = match.get("match_id", 0)
    if isinstance(match_id, int):
        return stage_index, match_id
    digits = "".join(ch for ch in str(match_id) if ch.isdigit())
    return stage_index, int(digits) if digits else str(match_id)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _score_text(match: Dict[str, Any]) -> str:
    home = match.get("home_goals") if match.get("home_goals") is not None else match.get("home_score")
    away = match.get("away_goals") if match.get("away_goals") is not None else match.get("away_score")
    if home is None or away is None:
        return "TBD"
    base = f"{home}-{away}"
    if match.get("penalties") and match.get("penalty_score"):
        return f"{base} ({match['penalty_score']} pens)"
    if match.get("extra_time"):
        return f"{base} AET"
    return base


@dataclass
class TeamJourneySummary:
    team: str
    simulations: int
    titles_won: int
    average_finish: str
    average_goals_for: float
    average_goals_against: float
    clean_sheets: int
    elimination_distribution: Dict[str, int]
    win_probability: float


class AdvancedMatchIntelligenceEngine:
    """Generate team-level timelines and narrative summaries."""

    def __init__(self, seed: int = 2026):
        self._seed = seed
        self._timeline_engine = LiveTimelineEngine()
        self._momentum_engine = MatchMomentumEngine()
        self._play_as_mode = PlayAsTeamMode()

    def enrich_match(self, match: Dict[str, Any], team_state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return a team-level intelligence payload for a finished match."""
        match_copy = dict(match)
        home_team = str(match_copy.get("home_team", "TBD"))
        away_team = str(match_copy.get("away_team", "TBD"))
        stage = _normalize_stage(str(match_copy.get("stage", "")))
        rng = random.Random(f"{self._seed}:{match_copy.get('match_id')}:{home_team}:{away_team}:{stage}")

        home_goals = _safe_int(match_copy.get("home_goals", match_copy.get("home_score")))
        away_goals = _safe_int(match_copy.get("away_goals", match_copy.get("away_score")))
        home_xg = float(match_copy.get("home_xg", 0.0) or 0.0)
        away_xg = float(match_copy.get("away_xg", 0.0) or 0.0)
        home_win_prob = float(match_copy.get("home_win_prob", 0.33) or 0.33)
        away_win_prob = float(match_copy.get("away_win_prob", 0.33) or 0.33)
        extra_time = bool(match_copy.get("extra_time", False))
        penalties = bool(match_copy.get("penalties", False))

        home_state = (team_state or {}).get(home_team, {}) if isinstance(team_state, dict) else {}
        away_state = (team_state or {}).get(away_team, {}) if isinstance(team_state, dict) else {}

        tactical_profile = TACTICAL_PROFILES.get(home_team, DEFAULT_TACTICAL_PROFILE)
        away_tactical = TACTICAL_PROFILES.get(away_team, DEFAULT_TACTICAL_PROFILE)

        match_states = self._momentum_engine.build_match_states(
            home_state=home_state,
            away_state=away_state,
            home_tactical=tactical_profile,
            away_tactical=away_tactical,
            stage=stage,
            extra_time=extra_time,
            penalties=penalties,
            rng=rng,
        )

        timeline = self._timeline_engine.generate_timeline(
            rng=rng,
            home_team=home_team,
            away_team=away_team,
            home_goals=home_goals,
            away_goals=away_goals,
            home_xg=home_xg,
            away_xg=away_xg,
            extra_time=extra_time,
            penalties=penalties,
            stage=stage,
            home_state=home_state,
            away_state=away_state,
            home_tactical=tactical_profile,
            away_tactical=away_tactical,
        )
        possession_trace = self._momentum_engine.build_possession_trace(match_states)
        momentum_trace = self._momentum_engine.build_momentum_trace(
            match_states=match_states,
            timeline=timeline,
            home_team=home_team,
            away_team=away_team,
        )
        xg_progression = self._momentum_engine.build_xg_progression(home_xg, away_xg, match_states)

        enriched = {
            **match_copy,
            "stage": stage,
            "stage_label": _stage_label(stage),
            "timeline": timeline,
            "match_states": match_states,
            "possession_trace": possession_trace,
            "momentum_trace": momentum_trace,
            "xg_progression": xg_progression,
            "momentum_summary": self._momentum_engine.summarize_match_momentum(timeline, momentum_trace),
            "analyst_summary": self._build_analyst_summary(
                home_team=home_team,
                away_team=away_team,
                stage=stage,
                home_goals=home_goals,
                away_goals=away_goals,
                home_xg=home_xg,
                away_xg=away_xg,
                home_win_prob=home_win_prob,
                away_win_prob=away_win_prob,
                extra_time=extra_time,
                penalties=penalties,
                home_state=home_state,
                away_state=away_state,
                timeline=timeline,
            ),
        }
        return enriched

    def build_team_journey(self, team_name: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Build a selected-team journey from a tournament state."""
        team_matches: List[Dict[str, Any]] = []
        for match in sorted(state.get("matches", []), key=_match_sort_key):
            if match.get("home_team") != team_name and match.get("away_team") != team_name:
                continue
            enriched = self.enrich_match(match, state.get("team_state", {}))
            team_matches.append(self._project_team_view(team_name, enriched))

        goals_for = sum(_safe_int(match.get("goals_for", 0)) for match in team_matches)
        goals_against = sum(_safe_int(match.get("goals_against", 0)) for match in team_matches)
        wins = sum(1 for match in team_matches if match.get("result") == "win")
        clean_sheets = sum(1 for match in team_matches if _safe_int(match.get("goals_against", 0)) == 0)
        stage_reached = team_matches[-1].get("stage_reached") if team_matches else "Not started"

        return {
            "team": team_name,
            "matches": team_matches,
            "goals_for": goals_for,
            "goals_against": goals_against,
            "wins": wins,
            "clean_sheets": clean_sheets,
            "stage_reached": stage_reached,
            "narrative": self._build_team_narrative(team_name, team_matches),
            "momentum_summary": self._build_momentum_summary(team_matches),
        }

    def summarize_play_as(self, team_name: str, journeys: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate a 10-simulation play-as run."""
        return self._play_as_mode.summarize(team_name, journeys)

    def _project_team_view(self, team_name: str, match: Dict[str, Any]) -> Dict[str, Any]:
        home_team = match.get("home_team")
        away_team = match.get("away_team")
        team_is_home = home_team == team_name
        team_goals = _safe_int(match.get("home_goals" if team_is_home else "away_goals"))
        opponent_goals = _safe_int(match.get("away_goals" if team_is_home else "home_goals"))
        result = "win" if team_goals > opponent_goals else "loss" if team_goals < opponent_goals else "draw"

        if match.get("stage") == "FINAL" and result == "win":
            stage_reached = "Champion"
        elif match.get("stage") == "FINAL" and result != "win":
            stage_reached = "Runner-up"
        elif match.get("stage") == "THIRD_PLACE":
            stage_reached = "Third Place" if result == "win" else "Fourth Place"
        elif match.get("stage") == "SF" and result == "loss":
            stage_reached = "Semi-Final"
        elif match.get("stage") == "QF" and result == "loss":
            stage_reached = "Quarter-Final"
        elif match.get("stage") == "R16" and result == "loss":
            stage_reached = "Round of 16"
        elif match.get("stage") == "R32" and result == "loss":
            stage_reached = "Round of 32"
        else:
            stage_reached = _stage_label(match.get("stage", "GROUP"))

        return {
            "match_id": match.get("match_id"),
            "stage": match.get("stage"),
            "stage_label": match.get("stage_label"),
            "stage_reached": stage_reached,
            "opponent": away_team if team_is_home else home_team,
            "is_home": team_is_home,
            "score": _score_text(match),
            "goals_for": team_goals,
            "goals_against": opponent_goals,
            "result": result,
            "extra_time": bool(match.get("extra_time", False)),
            "penalties": bool(match.get("penalties", False)),
            "penalty_score": match.get("penalty_score"),
            "timeline": match.get("timeline", []),
            "momentum_trace": match.get("momentum_trace", []),
            "possession_trace": match.get("possession_trace", []),
            "xg_progression": match.get("xg_progression", []),
            "analyst_summary": match.get("analyst_summary", {}),
        }

    def _build_team_narrative(self, team_name: str, matches: List[Dict[str, Any]]) -> str:
        if not matches:
            return f"{team_name} had no matches in this simulation."

        wins = sum(1 for match in matches if match.get("result") == "win")
        losses = sum(1 for match in matches if match.get("result") == "loss")
        goals_for = sum(_safe_int(match.get("goals_for", 0)) for match in matches)
        goals_against = sum(_safe_int(match.get("goals_against", 0)) for match in matches)
        late_drama = sum(1 for match in matches if match.get("extra_time") or match.get("penalties"))
        best_stage = matches[-1].get("stage_reached", "Group Stage")

        return (
            f"{team_name} finished at {best_stage} with {wins} wins and {losses} losses. "
            f"The team scored {goals_for} and conceded {goals_against}, with {late_drama} high-drama matches."
        )

    def _build_momentum_summary(self, matches: List[Dict[str, Any]]) -> str:
        if not matches:
            return "No momentum data available."
        shifts = sum(
            1
            for match in matches
            for event in match.get("timeline", [])
            if event.get("event_type") == "Momentum Shift"
        )
        pressure = sum(
            1
            for match in matches
            for event in match.get("timeline", [])
            if event.get("event_type") in {"Tactical Pressure", "Possession Domination"}
        )
        return f"Momentum swung {shifts} times with {pressure} sustained pressure phases across the tournament path."

    def _build_analyst_summary(
        self,
        *,
        home_team: str,
        away_team: str,
        stage: str,
        home_goals: int,
        away_goals: int,
        home_xg: float,
        away_xg: float,
        home_win_prob: float,
        away_win_prob: float,
        extra_time: bool,
        penalties: bool,
        home_state: Dict[str, Any],
        away_state: Dict[str, Any],
        timeline: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        favorite = home_team if home_win_prob >= away_win_prob else away_team
        winner = home_team if home_goals > away_goals else away_team if away_goals > home_goals else "Draw"
        balance = abs(home_xg - away_xg)
        upset = winner != "Draw" and winner != favorite and abs(home_win_prob - away_win_prob) > 0.10
        fatigue_note = "fatigue rose late" if (home_state.get("fatigue", 0) or away_state.get("fatigue", 0)) else "fresh enough to sustain tempo"

        pre_match = (
            f"{home_team} and {away_team} entered with a tactical balance gap of {balance:.2f} xG, "
            f"and {favorite} were favoured on the pre-match numbers."
        )
        post_match = (
            f"{winner if winner != 'Draw' else 'The match'} controlled the decisive moments; {fatigue_note}, "
            f"and the rhythm shifted most strongly through team-level momentum swings."
        )
        tactical = (
            f"{home_team} versus {away_team} featured a {stage.lower()}-stage tempo shaped by possession control, "
            f"pressure spells, and {('extra time' if extra_time else 'regulation pace')}."
        )
        if penalties:
            tactical += " The match required a penalty shootout to resolve the tie."

        return {
            "pre_match": pre_match,
            "post_match": post_match,
            "tactical_summary": tactical,
            "upset_explanation": (
                f"{winner} outperformed the pre-match favourite by converting pressure into control." if upset else ""
            ),
            "key_messages": self._extract_key_messages(timeline),
        }

    def _extract_key_messages(self, timeline: List[Dict[str, Any]]) -> List[str]:
        messages = []
        for event in timeline:
            label = event.get("label") or event.get("event_type")
            team = event.get("team")
            minute = event.get("minute")
            if label and team:
                messages.append(f"{minute} {label} — {team}")
            elif label:
                messages.append(f"{minute} {label}" if minute else str(label))
        return messages[:6]

    def _build_timeline(
        self,
        *,
        rng: random.Random,
        home_team: str,
        away_team: str,
        home_goals: int,
        away_goals: int,
        home_xg: float,
        away_xg: float,
        extra_time: bool,
        penalties: bool,
        home_state: Dict[str, Any],
        away_state: Dict[str, Any],
        home_tactical: Dict[str, Any],
        away_tactical: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        timeline: List[Dict[str, Any]] = []
        total_goals = home_goals + away_goals
        if total_goals > 0:
            scoring_order = self._scoreing_order(home_team, away_team, home_goals, away_goals, home_xg, away_xg)
            minutes = self._goal_minutes(rng, total_goals, extra_time)
            for idx, team in enumerate(scoring_order):
                minute = minutes[idx]
                label = "Penalty Goal" if penalties and minute.startswith("120") else "GOAL"
                timeline.append({
                    "minute": minute,
                    "event_type": label,
                    "team": team,
                    "label": label,
                })

        warning_chance = 0.30 + 0.08 * max(home_state.get("fatigue", 0.0), away_state.get("fatigue", 0.0))
        if rng.random() < warning_chance:
            timeline.append({
                "minute": self._minute_label(rng.randint(28, 76)),
                "event_type": "Yellow Card Accumulation Warning",
                "team": home_team if home_xg >= away_xg else away_team,
                "label": "Yellow Card Accumulation Warning",
            })

        red_card_chance = 0.08 + 0.04 * abs(home_xg - away_xg)
        if rng.random() < red_card_chance:
            timeline.append({
                "minute": self._minute_label(rng.randint(40, 82)),
                "event_type": "Red Card",
                "team": away_team if home_xg > away_xg else home_team,
                "label": "Red Card",
            })

        pressure_team = home_team if home_xg >= away_xg else away_team
        counter_team = away_team if pressure_team == home_team else home_team
        timeline.extend([
            {
                "minute": self._minute_label(rng.randint(18, 48)),
                "event_type": "Momentum Shift",
                "team": pressure_team,
                "label": "Momentum Shift",
                "note": f"{pressure_team} dominating possession",
            },
            {
                "minute": self._minute_label(rng.randint(55, 78)),
                "event_type": "Tactical Pressure",
                "team": pressure_team,
                "label": "Tactical Pressure",
                "note": f"{pressure_team} pushing aggressively",
            },
        ])

        if total_goals <= 1 or abs(home_xg - away_xg) < 0.35:
            timeline.append({
                "minute": self._minute_label(rng.randint(20, 70)),
                "event_type": "Counterattack Phase",
                "team": counter_team,
                "label": "Counterattack Phase",
            })

        if home_goals != away_goals and abs(home_goals - away_goals) >= 2:
            timeline.append({
                "minute": self._minute_label(rng.randint(60, 88)),
                "event_type": "Defensive Collapse",
                "team": away_team if home_goals > away_goals else home_team,
                "label": "Defensive Collapse",
            })

        if extra_time:
            timeline.append({
                "minute": "91'",
                "event_type": "Extra Time Begins",
                "team": "Match",
                "label": "Extra Time Begins",
            })
        if penalties:
            timeline.append({
                "minute": "120'",
                "event_type": "Penalty Shootout Begins",
                "team": "Match",
                "label": "Penalty Shootout Begins",
            })

        timeline.sort(key=lambda event: self._timeline_sort_key(event.get("minute", "0'")))
        return timeline

    def _goal_minutes(self, rng: random.Random, goals: int, extra_time: bool) -> List[str]:
        if goals <= 0:
            return []
        pool = list(range(7, 90))
        minutes = sorted(rng.sample(pool, k=min(goals, len(pool))))
        minutes = sorted(minutes)[:goals]
        return [self._minute_label(minute) for minute in minutes]

    def _scoreing_order(
        self,
        home_team: str,
        away_team: str,
        home_goals: int,
        away_goals: int,
        home_xg: float,
        away_xg: float,
    ) -> List[str]:
        counts = [(home_team, home_goals), (away_team, away_goals)]
        if home_goals == away_goals:
            first = home_team if home_xg >= away_xg else away_team
            second = away_team if first == home_team else home_team
            order = []
            for idx in range(home_goals):
                order.append(first if idx % 2 == 0 else second)
            return order
        dominant = home_team if home_goals > away_goals else away_team
        trailing = away_team if dominant == home_team else home_team
        order: List[str] = [dominant] * abs(home_goals - away_goals)
        for team, count in counts:
            if team != dominant:
                order.extend([team] * count)
        if len(order) < home_goals + away_goals:
            order.extend([trailing] * ((home_goals + away_goals) - len(order)))
        return order[: home_goals + away_goals]

    def _build_possession_trace(
        self,
        rng: random.Random,
        home_xg: float,
        away_xg: float,
        home_goals: int,
        away_goals: int,
        extra_time: bool,
        penalties: bool,
    ) -> List[Dict[str, Any]]:
        trace = []
        base_home = 50.0 + (home_xg - away_xg) * 7.0
        base_home += (home_goals - away_goals) * 1.8
        base_home = max(36.0, min(64.0, base_home))
        for minute in [0, 15, 30, 45, 60, 75, 90]:
            swing = rng.uniform(-4.0, 4.0)
            if minute >= 60 and home_goals != away_goals:
                swing += 2.0 if home_goals > away_goals else -2.0
            if extra_time and minute >= 90:
                swing *= 0.6
            home = max(30.0, min(70.0, base_home + swing))
            away = 100.0 - home
            trace.append({"minute": self._minute_label(minute), "home": round(home, 1), "away": round(away, 1)})
        if extra_time:
            home = max(30.0, min(70.0, base_home + rng.uniform(-2.0, 2.0)))
            trace.append({"minute": "105'", "home": round(home, 1), "away": round(100.0 - home, 1)})
        if penalties:
            trace.append({"minute": "120'", "home": 50.0, "away": 50.0})
        return trace

    def _build_momentum_trace(
        self,
        rng: random.Random,
        home_xg: float,
        away_xg: float,
        home_goals: int,
        away_goals: int,
        timeline: List[Dict[str, Any]],
        extra_time: bool,
        penalties: bool,
    ) -> List[Dict[str, Any]]:
        goal_minutes = {event["minute"] for event in timeline if event.get("event_type") in {"GOAL", "Penalty Goal"}}
        trace = []
        home_momentum = 50.0 + (home_xg - away_xg) * 9.0
        home_momentum += (home_goals - away_goals) * 4.0
        for minute in [0, 15, 30, 45, 60, 75, 90]:
            swing = rng.uniform(-6.0, 6.0)
            if f"{minute}'" in goal_minutes:
                swing += 8.0 if home_goals >= away_goals else -8.0
            if minute >= 60 and away_goals > home_goals:
                swing -= 4.0
            value = max(10.0, min(90.0, home_momentum + swing))
            trace.append({"minute": self._minute_label(minute), "home": round(value, 1), "away": round(100.0 - value, 1)})
        if extra_time:
            home = max(10.0, min(90.0, home_momentum + rng.uniform(-3.0, 3.0)))
            trace.append({"minute": "105'", "home": round(home, 1), "away": round(100.0 - home, 1)})
        if penalties:
            trace.append({"minute": "120'", "home": 50.0, "away": 50.0})
        return trace

    def _build_xg_progression(
        self,
        home_xg: float,
        away_xg: float,
        extra_time: bool,
        penalties: bool,
    ) -> List[Dict[str, Any]]:
        progression = []
        steps = [0, 15, 30, 45, 60, 75, 90]
        for idx, minute in enumerate(steps, 1):
            factor = idx / len(steps)
            progression.append({
                "minute": self._minute_label(minute),
                "home": round(home_xg * factor, 2),
                "away": round(away_xg * factor, 2),
            })
        if extra_time:
            progression.append({"minute": "105'", "home": round(home_xg * 1.08, 2), "away": round(away_xg * 1.08, 2)})
        if penalties:
            progression.append({"minute": "120'", "home": round(home_xg * 1.08, 2), "away": round(away_xg * 1.08, 2)})
        return progression

    def _timeline_sort_key(self, minute: str) -> int:
        if minute.endswith("'"):
            base = minute[:-1]
        else:
            base = minute
        if "+" in base:
            start, extra = base.split("+", 1)
            return int(start) * 10 + int(extra)
        try:
            return int(base) * 10
        except Exception:
            return 9999

    def _minute_label(self, minute: int) -> str:
        if minute in {105, 120}:
            return f"{minute}'"
        if minute > 90:
            return f"90+{minute - 90}'"
        return f"{minute}'"


def build_team_journey_summary(team_name: str, journeys: Iterable[Dict[str, Any]]) -> TeamJourneySummary:
    journeys = list(journeys)
    titles_won = sum(1 for journey in journeys if journey.get("stage_reached") == "Champion")
    elimination_distribution = Counter(journey.get("stage_reached", "Unknown") for journey in journeys)
    if not journeys:
        return TeamJourneySummary(team_name, 0, 0, "N/A", 0.0, 0.0, 0, {})
    average_finish = sorted(elimination_distribution.items(), key=lambda item: item[0])[0][0]
    average_goals_for = sum(float(journey.get("goals_for", 0)) for journey in journeys) / len(journeys)
    average_goals_against = sum(float(journey.get("goals_against", 0)) for journey in journeys) / len(journeys)
    clean_sheets = sum(int(journey.get("clean_sheets", 0)) for journey in journeys)
    return TeamJourneySummary(
        team=team_name,
        simulations=len(journeys),
        titles_won=titles_won,
        average_finish=average_finish,
        average_goals_for=round(average_goals_for, 2),
        average_goals_against=round(average_goals_against, 2),
        clean_sheets=clean_sheets,
        elimination_distribution=dict(elimination_distribution),
        win_probability=round(titles_won / len(journeys), 3),
    )
