"""Team-level live timeline generation for tournament matches."""

from __future__ import annotations

import random
from typing import Any, Dict, List, Tuple


class LiveTimelineEngine:
    """Generate football-authentic timeline events at team level."""

    def generate_timeline(
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
        stage: str,
        home_state: Dict[str, Any],
        away_state: Dict[str, Any],
        home_tactical: Dict[str, Any],
        away_tactical: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        timeline: List[Dict[str, Any]] = []
        total_goals = max(0, int(home_goals) + int(away_goals))

        scoring_order = self._scoring_order(
            home_team=home_team,
            away_team=away_team,
            home_goals=home_goals,
            away_goals=away_goals,
            home_xg=home_xg,
            away_xg=away_xg,
            home_tactical=home_tactical,
            away_tactical=away_tactical,
        )
        goal_minutes = self._goal_minutes(rng, total_goals, extra_time)

        running_home = 0
        running_away = 0
        final_winner = home_team if home_goals > away_goals else away_team if away_goals > home_goals else "Draw"

        for idx, team in enumerate(scoring_order):
            if idx >= len(goal_minutes):
                break
            minute = goal_minutes[idx]
            if team == home_team:
                running_home += 1
            else:
                running_away += 1

            label = "Goal"
            if penalties and minute == "120'":
                label = "Penalty Goal"
            elif running_home == running_away:
                label = "Equalizer"
            elif self._is_injury_time(minute):
                label = "Injury Time Goal"
            elif self._is_late_winner(minute, team, final_winner, running_home, running_away):
                label = "Late Winner"

            timeline.append({
                "minute": minute,
                "event_type": label,
                "team": team,
                "label": label,
            })

        dominant_team = home_team if home_xg >= away_xg else away_team
        underdog_team = away_team if dominant_team == home_team else home_team
        dominant_gap = abs(home_xg - away_xg)

        timeline.append({
            "minute": self._minute_label(rng.randint(14, 28)),
            "event_type": "Possession Domination",
            "team": dominant_team,
            "label": "Possession Domination",
        })

        if dominant_gap >= 0.20:
            timeline.append({
                "minute": self._minute_label(rng.randint(32, 58)),
                "event_type": "Tactical Pressure",
                "team": dominant_team,
                "label": "Tactical Pressure",
                "note": f"{dominant_team} compressing space and forcing turnovers",
            })

        if dominant_gap <= 0.45 or total_goals <= 2:
            timeline.append({
                "minute": self._minute_label(rng.randint(40, 74)),
                "event_type": "Momentum Shift",
                "team": underdog_team,
                "label": "Momentum Shift",
            })

        if (home_tactical.get("style") in {"attacking", "pressing"} or away_tactical.get("style") in {"attacking", "pressing"}) and rng.random() < 0.65:
            timeline.append({
                "minute": self._minute_label(rng.randint(47, 81)),
                "event_type": "Counterattack Wave",
                "team": underdog_team,
                "label": "Counterattack Wave",
            })

        fatigue_pressure = max(float(home_state.get("fatigue", 0.0)), float(away_state.get("fatigue", 0.0)))
        aggression = max(float(home_state.get("tactical_intensity", 1.0)), float(away_state.get("tactical_intensity", 1.0)))

        yellow_chance = min(0.72, 0.26 + fatigue_pressure * 0.70 + max(0.0, aggression - 1.0) * 0.35)
        if rng.random() < yellow_chance:
            timeline.append({
                "minute": self._minute_label(rng.randint(24, 79)),
                "event_type": "Yellow Card Warning",
                "team": underdog_team if dominant_gap > 0.25 else dominant_team,
                "label": "Yellow Card Warning",
            })

        knockout_pressure = 0.0
        if stage in {"R32", "R16"}:
            knockout_pressure = 0.04
        elif stage == "QF":
            knockout_pressure = 0.08
        elif stage in {"SF", "FINAL"}:
            knockout_pressure = 0.11
        red_chance = min(0.28, 0.05 + knockout_pressure + max(0.0, aggression - 1.0) * 0.10)
        if rng.random() < red_chance:
            timeline.append({
                "minute": self._minute_label(rng.randint(52, 86)),
                "event_type": "Red Card",
                "team": underdog_team,
                "label": "Red Card",
            })

        if abs(home_goals - away_goals) >= 2:
            timeline.append({
                "minute": self._minute_label(rng.randint(63, 88)),
                "event_type": "Defensive Collapse",
                "team": away_team if home_goals > away_goals else home_team,
                "label": "Defensive Collapse",
            })

        if extra_time:
            timeline.append({
                "minute": "91'",
                "event_type": "Extra Time Start",
                "team": "Match",
                "label": "Extra Time Start",
            })
        if penalties:
            timeline.append({
                "minute": "120'",
                "event_type": "Penalty Shootout Start",
                "team": "Match",
                "label": "Penalty Shootout Start",
            })

        timeline.sort(key=lambda event: self.timeline_sort_key(event.get("minute", "0'")))
        return self._dedupe_events(timeline)

    def _scoring_order(
        self,
        *,
        home_team: str,
        away_team: str,
        home_goals: int,
        away_goals: int,
        home_xg: float,
        away_xg: float,
        home_tactical: Dict[str, Any],
        away_tactical: Dict[str, Any],
    ) -> List[str]:
        total = max(0, int(home_goals) + int(away_goals))
        if total == 0:
            return []

        if home_goals == away_goals:
            first = home_team if home_xg >= away_xg else away_team
            second = away_team if first == home_team else home_team
            order: List[str] = []
            for idx in range(total):
                order.append(first if idx % 2 == 0 else second)
            return order

        dominant = home_team if home_goals > away_goals else away_team
        trailing = away_team if dominant == home_team else home_team
        dominant_goals = max(home_goals, away_goals)
        trailing_goals = min(home_goals, away_goals)

        dominant_style = home_tactical if dominant == home_team else away_tactical
        start_fast = dominant_style.get("style") in {"attacking", "pressing", "balanced_attack"}

        order: List[str] = []
        if start_fast and dominant_goals > 0:
            order.append(dominant)
            dominant_goals -= 1

        for _ in range(trailing_goals):
            order.append(trailing)
            if dominant_goals > 0:
                order.append(dominant)
                dominant_goals -= 1

        if dominant_goals > 0:
            order.extend([dominant] * dominant_goals)

        return order[:total]

    def _goal_minutes(self, rng: random.Random, goals: int, extra_time: bool) -> List[str]:
        if goals <= 0:
            return []

        base_pool = list(range(6, 90))
        sampled = sorted(rng.sample(base_pool, k=min(goals, len(base_pool))))

        if goals >= 2 and rng.random() < 0.40:
            sampled[-1] = rng.randint(90, 95)
        if goals >= 3 and rng.random() < 0.30:
            sampled[-2] = rng.randint(85, 92)

        sampled = sorted(sampled)[:goals]
        return [self._minute_label(minute, extra_time=extra_time) for minute in sampled]

    def _is_late_winner(self, minute: str, team: str, final_winner: str, home_score: int, away_score: int) -> bool:
        if team != final_winner or final_winner == "Draw":
            return False
        minute_value = self.timeline_sort_key(minute)
        if minute_value < self.timeline_sort_key("85'"):
            return False
        return abs(home_score - away_score) == 1

    @staticmethod
    def _is_injury_time(minute: str) -> bool:
        return "90+" in minute

    def _dedupe_events(self, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: set[Tuple[str, str, str]] = set()
        filtered: List[Dict[str, Any]] = []
        for event in timeline:
            key = (str(event.get("minute")), str(event.get("event_type")), str(event.get("team")))
            if key in seen:
                continue
            seen.add(key)
            filtered.append(event)
        return filtered[:14]

    def timeline_sort_key(self, minute: str) -> int:
        token = minute[:-1] if minute.endswith("'") else minute
        if "+" in token:
            base, extra = token.split("+", 1)
            return int(base) * 10 + int(extra)
        try:
            return int(token) * 10
        except Exception:
            return 9999

    @staticmethod
    def _minute_label(minute: int, extra_time: bool = False) -> str:
        """
        Format minute display:
        - If extra_time=True and minute > 90: show as real time (95' not 90+5')
        - If extra_time=False and minute > 90: show as 90+x format
        - Special: 105' and 120' always shown as real time
        """
        if minute in {105, 120}:
            return f"{minute}'"
        if minute > 90:
            # If match went to extra time, show real minute (91-120)
            if extra_time:
                return f"{minute}'"
            # If no extra time, show as 90+x format
            else:
                return f"90+{minute - 90}'"
        return f"{minute}'"
