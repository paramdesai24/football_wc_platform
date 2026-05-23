"""
Knockout Match Engine — Phase 4.2 (Final Realism Polish)
==========================================================
Simulates knockout-stage matches with football-authentic drama:

  Regulation (90 min)
    ↓ if draw →
  Extra Time (30 min, reduced xG)
    ↓ if draw →
  Penalty Shootout (specialist-adjusted)

Key calibration layers (Phase 4.2):
  • Tactical Team Identities  — team style shapes xG, draw tendency, ET likelihood
  • Balanced-match compression — tight games compress toward draws → more ET
  • Stage-specific ET boost    — later rounds become cagier → more 0-0/1-1
  • Round fatigue              — xG falls progressively through the bracket
  • Goal-cap suppression       — no 4-0 finals; stage-aware ceiling
  • Penalty specialists        — Croatia/Germany/Argentina overperform
  • Dark-horse regression      — non-elite teams regress in QF+
  • Controlled upsets          — upset_context() weights, not pure noise
  • Frontend flags             — is_upset, is_dramatic, result_type enrichment
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]))

from match_engine.probabilities.match_probability import MatchProbabilityEngine
from ..utils.team_state import apply_team_state, soft_cap_goals, update_team_state
from ..utils.constants import (
    EXTRA_TIME_SCORING_FACTOR,
    EXTRA_TIME_MINUTES_RATIO,
    PENALTY_BASE_SCORE_PROB,
    PENALTY_ROUNDS,
    PENALTY_SUDDEN_DEATH_MAX,
    HOST_CONFEDERATION,
    HOST_CONTINENT_XG_BOOST,
    TEAM_NAME_ALIASES,
    # Phase 4.2
    ELITE_TEAMS,
    TOURNAMENT_PEDIGREE,
    STAGE_VOLATILITY_SCALING,
    STAGE_ET_BOOST,
    STAGE_GOAL_CAP,
    ROUND_FATIGUE_FACTOR,
    DARK_HORSE_REGRESSION_FACTOR,
    PENALTY_ELITE_BOOST,
    PENALTY_SPECIALIST,
    TEAM_STYLE,
    DEFAULT_TEAM_STYLE,
    TACTICAL_BALANCE_THRESHOLD,
    TACTICAL_COMPRESSION_RATE,
    REGULATION_DRAW_BREAK_PROB,
    ET_DRAW_BREAK_PROB,
)

logger = logging.getLogger("tournament.knockouts")


class KnockoutMatchEngine:
    """
    FIFA World Cup knockout match simulator — Phase 4.2 Final Realism Polish.

    Design principles:
      - Quality matters, but football is never deterministic
      - Elite teams handle pressure better (pedigree boost, composure)
      - Tactical identity shapes each match's narrative
      - Draw probability is amplified in balanced, later-round games
      - Penalties reflect team history, not just a coin flip
    """

    def __init__(self, prediction_engine: Optional[MatchProbabilityEngine] = None,
                 seed: Optional[int] = None):
        self._engine = prediction_engine or MatchProbabilityEngine()
        self._rng = np.random.default_rng(seed)

    # ─────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────

    def resolve_name(self, name: str) -> str:
        """Resolve tournament display name → Phase 2 data name."""
        return TEAM_NAME_ALIASES.get(name, name)

    def simulate(self, home_team: str, away_team: str,
                 match_id: int = 0, stage: str = "knockout",
                 team_state: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Simulate a knockout match. Always resolves a winner.

        Returns a rich dict with goals, xG, extra-time, penalties,
        winner/loser, and UI-ready flags (is_upset, is_dramatic).
        """
        h_resolved = self.resolve_name(home_team)
        a_resolved = self.resolve_name(away_team)

        # ── Phase 3: Base xG prediction ──────────────────────
        try:
            home_data = self._engine._loader.get_team(h_resolved)
            away_data = self._engine._loader.get_team(a_resolved)
            if home_data is None or away_data is None:
                raise ValueError(f"Missing team data for {home_team} vs {away_team}")

            home_snapshot = apply_team_state(home_data, team_state.get(home_team) if team_state else None)
            away_snapshot = apply_team_state(away_data, team_state.get(away_team) if team_state else None)

            prediction = self._engine.predict(
                h_resolved, a_resolved,
                venue="neutral",
                tournament=self._stage_to_tournament(stage),
                home_data=home_snapshot,
                away_data=away_snapshot,
            )
            raw_home_xg   = prediction.get("home_xg", 1.2)
            raw_away_xg   = prediction.get("away_xg", 1.2)
            home_win_prob = prediction.get("home_win_prob", 0.40)
            away_win_prob = prediction.get("away_win_prob", 0.40)
        except Exception as exc:
            logger.warning("Prediction error %s vs %s: %s", home_team, away_team, exc)
            raw_home_xg, raw_away_xg = 1.2, 1.2
            home_win_prob, away_win_prob = 0.45, 0.45

        # ── Phase 4.2: Calibration Stack ──────────────────────
        home_xg, away_xg = self._apply_calibration(
            home_team, away_team, raw_home_xg, raw_away_xg, stage, team_state=team_state
        )

        # ── Regulation (90 min) ───────────────────────────────
        home_goals, away_goals = self._simulate_regulation(
            home_xg, away_xg, home_team, away_team, stage
        )
        home_goals = soft_cap_goals(home_goals, stage)
        away_goals = soft_cap_goals(away_goals, stage)

        extra_time   = False
        penalties    = False
        penalty_score = None
        et_home = et_away = 0

        # ── Extra Time (if draw after 90) ────────────────────────────────
        if home_goals == away_goals:
            # Late decisive goal: breaks the draw in regulation ~55% of the time.
            # Represents the 90th-minute winner rather than a drift to ET.
            if self._rng.random() < REGULATION_DRAW_BREAK_PROB:
                # Award goal to team with xG advantage; coin-flip if equal
                if home_xg > away_xg + 0.05:
                    home_goals += 1
                elif away_xg > home_xg + 0.05:
                    away_goals += 1
                else:
                    if self._rng.random() < 0.5:
                        home_goals += 1
                    else:
                        away_goals += 1
            else:
                extra_time = True
                et_home, et_away = self._simulate_extra_time(
                    home_xg, away_xg, home_team, away_team, stage
                )
                home_goals += et_home
                away_goals += et_away

        # ── Penalties (if still draw after ET) ────────────────
        if home_goals == away_goals:
            # Golden moment: 30% chance of decisive ET goal before pens
            if extra_time and self._rng.random() < ET_DRAW_BREAK_PROB:
                if home_xg > away_xg + 0.05:
                    home_goals += 1
                elif away_xg > home_xg + 0.05:
                    away_goals += 1
                else:
                    if self._rng.random() < 0.5:
                        home_goals += 1
                    else:
                        away_goals += 1

        if home_goals == away_goals:
            penalties = True
            pen_h, pen_a = self._simulate_penalties(
                home_team, away_team, home_win_prob, away_win_prob
            )
            penalty_score = f"{pen_h}-{pen_a}"

        # ── Determine winner ──────────────────────────────────
        if penalties:
            ph, pa = map(int, penalty_score.split("-"))
            winner = home_team if ph > pa else away_team
            loser  = away_team if ph > pa else home_team
        elif home_goals > away_goals:
            winner, loser = home_team, away_team
        else:
            winner, loser = away_team, home_team

        # ── UI flags ──────────────────────────────────────────
        favourite   = home_team if home_win_prob >= away_win_prob else away_team
        is_upset    = (winner != favourite) and (abs(home_win_prob - away_win_prob) > 0.10)
        is_dramatic = extra_time or penalties or (
            abs(home_goals - away_goals) <= 1 and home_goals + away_goals >= 2
        )

        home_state = team_state.get(home_team) if team_state else None
        away_state = team_state.get(away_team) if team_state else None
        update_team_state(home_state, home_goals, away_goals, stage, extra_time=extra_time, penalties=penalties, upset=is_upset)
        update_team_state(away_state, away_goals, home_goals, stage, extra_time=extra_time, penalties=penalties, upset=is_upset)

        result_type = "penalties" if penalties else \
                      "extra_time" if extra_time else "regulation"

        logger.info(
            "  M%d: %s %d-%d %s (%s)%s",
            match_id, home_team, home_goals, away_goals, away_team,
            stage,
            f" [PEN {penalty_score}]" if penalties else " [AET]" if extra_time else "",
        )

        return {
            "match_id":      match_id,
            "stage":         stage,
            "home_team":     home_team,
            "away_team":     away_team,
            "home_goals":    home_goals,
            "away_goals":    away_goals,
            "home_xg":       round(home_xg, 2),
            "away_xg":       round(away_xg, 2),
            "extra_time":    extra_time,
            "et_home_goals": et_home,
            "et_away_goals": et_away,
            "penalties":     penalties,
            "penalty_score": penalty_score,
            "winner":        winner,
            "loser":         loser,
            "home_win_prob": round(home_win_prob, 4),
            "away_win_prob": round(away_win_prob, 4),
            "result_type":   result_type,
            "is_upset":      is_upset,
            "is_dramatic":   is_dramatic,
        }

    # ─────────────────────────────────────────────────────────
    # CALIBRATION STACK (Phase 4.2)
    # ─────────────────────────────────────────────────────────

    def _apply_calibration(
        self, home: str, away: str,
        h_xg: float, a_xg: float, stage: str,
        team_state: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> Tuple[float, float]:
        """
        Apply all Phase 4.2 xG modifiers in order.

        Pipeline:
          1. Tactical team identity (style multiplier + opponent defence reduction)
          2. Tournament pedigree composure boost
          3. Round fatigue factor
          4. Dark-horse regression (QF+)
          5. Host-continent boost
          6. Volatility-aware lambda adjustment
          7. Balanced-match tactical compression → ET probability ↑
        """
        h_style = TEAM_STYLE.get(home, DEFAULT_TEAM_STYLE)
        a_style = TEAM_STYLE.get(away, DEFAULT_TEAM_STYLE)

        # 1. Tactical identity
        h_xg *= h_style["xg_mult"]
        a_xg *= a_style["xg_mult"]
        # Defensive solidity reduces opponent
        h_xg -= a_style["def_solid"]
        a_xg -= h_style["def_solid"]

        # 1b. Persistent team identity: offense, defense, form, fatigue, consistency.
        if team_state:
            h_state = team_state.get(home, {})
            a_state = team_state.get(away, {})

            h_off = float(h_state.get("offensive_rating", 1.0))
            h_def = float(h_state.get("defensive_rating", 1.0))
            h_form = float(h_state.get("form_modifier", 1.0))
            h_fatigue = float(h_state.get("fatigue", 0.0))
            h_consistency = float(h_state.get("consistency_factor", 1.0))

            a_off = float(a_state.get("offensive_rating", 1.0))
            a_def = float(a_state.get("defensive_rating", 1.0))
            a_form = float(a_state.get("form_modifier", 1.0))
            a_fatigue = float(a_state.get("fatigue", 0.0))
            a_consistency = float(a_state.get("consistency_factor", 1.0))

            h_xg *= h_off * h_form * h_consistency * (1.0 - 0.28 * h_fatigue)
            a_xg *= a_off * a_form * a_consistency * (1.0 - 0.28 * a_fatigue)

            # Suppress scoring further against elite defensive setups.
            h_xg *= max(0.78, 1.08 - max(a_def - 1.0, 0.0) * 0.22)
            a_xg *= max(0.78, 1.08 - max(h_def - 1.0, 0.0) * 0.22)

        # 2. Pedigree composure (small boost — keeps elite edge modest)
        h_xg += TOURNAMENT_PEDIGREE.get(home, 0)
        a_xg += TOURNAMENT_PEDIGREE.get(away, 0)

        # 3. Round fatigue
        fatigue = ROUND_FATIGUE_FACTOR.get(stage, 1.0)
        h_xg *= fatigue
        a_xg *= fatigue

        # 4. Dark-horse regression in QF+
        if stage in ("QF", "SF", "Final"):
            if home not in ELITE_TEAMS:
                h_xg *= DARK_HORSE_REGRESSION_FACTOR
            if away not in ELITE_TEAMS:
                a_xg *= DARK_HORSE_REGRESSION_FACTOR

        # 5. Host-continent boost
        h_conf = self._get_confederation(home)
        a_conf = self._get_confederation(away)
        if h_conf == HOST_CONFEDERATION:
            h_xg += HOST_CONTINENT_XG_BOOST
        if a_conf == HOST_CONFEDERATION:
            a_xg += HOST_CONTINENT_XG_BOOST

        # Floor before volatility scaling
        h_xg = max(h_xg, 0.20)
        a_xg = max(a_xg, 0.20)

        # 6. Volatility scaling (widens gap between stronger/weaker in later rounds)
        vol = STAGE_VOLATILITY_SCALING.get(stage, 1.0)
        if vol < 1.0 and h_xg != a_xg:
            leader, trailer = (h_xg, a_xg) if h_xg > a_xg else (a_xg, h_xg)
            gap = leader - trailer
            expand = (1.0 - vol) * gap
            if h_xg > a_xg:
                h_xg += expand
                a_xg = max(a_xg - expand, 0.20)
            else:
                a_xg += expand
                h_xg = max(h_xg - expand, 0.20)

        # 7. Tactical compression for balanced matchups
        #    When xG gap is small, compress both toward a cautious midpoint.
        #    This raises the probability of a regulation draw → more ET.
        gap = abs(h_xg - a_xg)
        if gap < TACTICAL_BALANCE_THRESHOLD:
            midpoint = (h_xg + a_xg) / 2.0
            # Apply stage ET boost as additional compression strength
            et_strength = STAGE_ET_BOOST.get(stage, 0.03)
            compression = TACTICAL_COMPRESSION_RATE + et_strength
            h_xg = h_xg + compression * (midpoint - h_xg)
            a_xg = a_xg + compression * (midpoint - a_xg)

        return max(h_xg, 0.15), max(a_xg, 0.15)

    # ─────────────────────────────────────────────────────────
    # REGULATION
    # ─────────────────────────────────────────────────────────

    def _simulate_regulation(
        self, h_xg: float, a_xg: float,
        home: str, away: str, stage: str
    ) -> Tuple[int, int]:
        """
        Simulate 90 min with Poisson draws + stage goal cap.

        Also applies tactical draw-affinity: a small probability
        that the scoreline is forced to a 0-0 or 1-1 before the
        Poisson draw, representing ultra-defensive tactical setups.
        """
        h_style = TEAM_STYLE.get(home, DEFAULT_TEAM_STYLE)
        a_style = TEAM_STYLE.get(away, DEFAULT_TEAM_STYLE)

        # Combined draw affinity (mean of both styles)
        draw_affinity = (h_style["draw_affinity"] + a_style["draw_affinity"]) / 2.0
        # Extra ET boost compresses further
        draw_affinity += STAGE_ET_BOOST.get(stage, 0.0) * 0.5

        # Tactical draw event: occasionally collapses to 0-0 or 1-1
        if self._rng.random() < draw_affinity:
            if self._rng.random() < 0.55:
                return 0, 0       # Goalless tactical draw
            else:
                return 1, 1       # 1-1 entertaining draw

        # Standard Poisson draw
        hg = int(self._rng.poisson(h_xg))
        ag = int(self._rng.poisson(a_xg))

        # Stage goal cap
        h_cap, a_cap = STAGE_GOAL_CAP.get(stage, (5, 5))
        hg = min(hg, h_cap)
        ag = min(ag, a_cap)

        return hg, ag

    # ─────────────────────────────────────────────────────────
    # EXTRA TIME
    # ─────────────────────────────────────────────────────────

    def _simulate_extra_time(
        self, h_xg: float, a_xg: float,
        home: str, away: str, stage: str
    ) -> Tuple[int, int]:
        """
        Simulate 30 min of extra time.

        Goals are rare:
          - Physical fatigue reduces intensity to ~35% of 90 min rate
          - Elite teams retain slight composure advantage
          - ET rarely produces more than 1 goal each
        """
        et_factor = EXTRA_TIME_SCORING_FACTOR * EXTRA_TIME_MINUTES_RATIO

        et_h = h_xg * et_factor
        et_a = a_xg * et_factor

        # Elite teams are slightly sharper in ET (depth of squad, experience)
        if home in ELITE_TEAMS:
            et_h *= 1.04
        if away in ELITE_TEAMS:
            et_a *= 1.04

        if self._rng.random() < 0.20:
            et_h *= 0.92
            et_a *= 0.92

        et_h = max(et_h, 0.04)
        et_a = max(et_a, 0.04)

        goals_h = int(self._rng.poisson(et_h))
        goals_a = int(self._rng.poisson(et_a))

        return min(goals_h, 2), min(goals_a, 2)

    # ─────────────────────────────────────────────────────────
    # PENALTY SHOOTOUT
    # ─────────────────────────────────────────────────────────

    def _simulate_penalties(
        self, home: str, away: str,
        home_prob: float, away_prob: float
    ) -> Tuple[int, int]:
        """
        Simulate a penalty shootout with specialist profiles.

        Scoring probability per kick is composed of:
          base rate (FIFA historical ~76%)
          + strength differential (small effect)
          + elite composure boost
          + specialist profile (Croatia +4%, England -3%, etc.)

        Result: shootouts feel tense, specialists matter subtly.
        """
        strength_diff = home_prob - away_prob

        h_pen = PENALTY_BASE_SCORE_PROB + strength_diff * 0.04
        a_pen = PENALTY_BASE_SCORE_PROB - strength_diff * 0.04

        # Elite composure
        if home in ELITE_TEAMS:
            h_pen += PENALTY_ELITE_BOOST
        if away in ELITE_TEAMS:
            a_pen += PENALTY_ELITE_BOOST

        # Specialist profiles
        h_pen += PENALTY_SPECIALIST.get(home, 0.0)
        a_pen += PENALTY_SPECIALIST.get(away, 0.0)

        h_pen = float(np.clip(h_pen, 0.62, 0.92))
        a_pen = float(np.clip(a_pen, 0.62, 0.92))

        home_score = away_score = 0

        # 5 rounds
        for i in range(PENALTY_ROUNDS):
            if self._rng.random() < h_pen:
                home_score += 1
            if self._rng.random() < a_pen:
                away_score += 1

            # Early termination
            remaining = PENALTY_ROUNDS - (i + 1)
            if i >= 2:
                if home_score > away_score + remaining:
                    break
                if away_score > home_score + remaining:
                    break

        # Sudden death
        sd = 0
        while home_score == away_score and sd < PENALTY_SUDDEN_DEATH_MAX:
            h_scored = self._rng.random() < h_pen
            a_scored = self._rng.random() < a_pen
            if h_scored:
                home_score += 1
            if a_scored:
                away_score += 1
            if h_scored != a_scored:
                break
            sd += 1

        # Final coin flip (should be extremely rare)
        if home_score == away_score:
            if self._rng.random() < 0.5:
                home_score += 1
            else:
                away_score += 1

        return home_score, away_score

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────

    def _stage_to_tournament(self, stage: str) -> str:
        """Map bracket stage → Phase 3 tournament context key."""
        return {
            "R32":       "world_cup_r16",
            "R16":       "world_cup_r16",
            "QF":        "world_cup_quarter",
            "SF":        "world_cup_semi",
            "3rd_place": "world_cup_semi",
            "Final":     "world_cup_final",
        }.get(stage, "world_cup_r16")

    def _get_confederation(self, team: str) -> str:
        """Return team's confederation string for host-boost check."""
        try:
            data = self._engine._loader.get_team(self.resolve_name(team).lower())
            if data:
                return data.get("confederation", "")
        except Exception:
            pass
        return ""
