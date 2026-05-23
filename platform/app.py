"""
WC26 Intelligence Platform - Streamlit Frontend
Dark-themed tournament dashboard with predictions, rankings, analytics, and overrides.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

import pandas as pd
import streamlit as st


sys.path.insert(0, str(Path(__file__).parent / "backend-api"))
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.flags import format_team_display


BACKEND_BASE = os.getenv("BACKEND_BASE", "http://localhost:8000")

TEAMS = {
    "Spain": "C_ES",
    "France": "C_FR",
    "Argentina": "C_AR",
    "Germany": "C_DE",
    "Brazil": "C_BR",
    "England": "C_GB-ENG",
    "Portugal": "C_PT",
    "Netherlands": "C_NL",
    "Italy": "C_IT",
    "Belgium": "C_BE",
    "Uruguay": "C_UY",
    "Colombia": "C_CO",
}
TEAM_NAMES = list(TEAMS.keys())
STAGE_ORDER = ["GROUP", "R32", "R16", "QF", "SF", "THIRD_PLACE", "FINAL"]


st.set_page_config(
    page_title="WC26 Intelligence Platform",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


BACKEND_BASE = os.getenv("BACKEND_BASE", BACKEND_BASE)


def http_get(path: str, timeout: int = 30):
    url = f"{BACKEND_BASE}{path}"
    try:
        with urllib_request.urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, HTTPError) as error:
        return {"error": str(error)}
    except Exception as error:
        return {"error": str(error)}


def http_post(path: str, payload: Dict[str, Any], timeout: int = 120):
    url = f"{BACKEND_BASE}{path}"
    data = json.dumps(payload).encode("utf-8")
    request = urllib_request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib_request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, HTTPError) as error:
        return {"error": str(error)}
    except Exception as error:
        return {"error": str(error)}


def as_data_frame(rows: Any) -> pd.DataFrame:
    if isinstance(rows, pd.DataFrame):
        return rows
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def display_data_frame(rows: Any) -> pd.DataFrame:
    frame = as_data_frame(rows)
    if frame.empty:
        return frame

    display_frame = frame.copy()
    for column in display_frame.columns:
        if display_frame[column].dtype == object:
            display_frame[column] = display_frame[column].map(lambda value: format_team_display(value) if isinstance(value, str) else value)
    return display_frame


def normalize_state(response: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(response, dict):
        return {}
    data = response.get("data")
    if isinstance(data, dict):
        return data
    if isinstance(response, dict):
        return response
    return {}


def stage_rank(stage: str) -> int:
    return STAGE_ORDER.index(stage) if stage in STAGE_ORDER else len(STAGE_ORDER)


def score_text(match: Dict[str, Any]) -> str:
    home_score = match.get("home_score")
    away_score = match.get("away_score")
    if home_score is None or away_score is None:
        return "TBD"
    base = f"{home_score}-{away_score}"
    if match.get("penalties") and match.get("penalty_score"):
        return f"{base} ({match['penalty_score']} pens)"
    if match.get("extra_time"):
        return f"{base} AET"
    return base


def stage_title(stage: str) -> str:
    return {
        "GROUP": "Group Stage",
        "R32": "Round of 32",
        "R16": "Round of 16",
        "QF": "Quarter-Finals",
        "SF": "Semi-Finals",
        "THIRD_PLACE": "Third-Place Match",
        "FINAL": "Final",
    }.get(stage, stage)


def team_code(team_name: str) -> str:
    name = str(team_name or "").strip()
    mapping = {
        "Argentina": "ARG",
        "Germany": "GER",
        "Brazil": "BRA",
        "Spain": "ESP",
        "France": "FRA",
        "England": "ENG",
        "Portugal": "POR",
        "Netherlands": "NED",
        "Italy": "ITA",
        "Belgium": "BEL",
        "Uruguay": "URU",
        "Colombia": "COL",
        "Uzbekistan": "UZB",
        "Ghana": "GHA",
    }
    return mapping.get(name, name[:3].upper() if name else "TBD")


def match_caption(match: Dict[str, Any]) -> str:
    winner = match.get("winner") or "TBD"
    return f"Winner: {format_team_display(winner)}"


def format_journey_scoreline(match: Dict[str, Any], selected_team: str) -> str:
    team_is_home = bool(match.get("is_home", False))
    opponent = str(match.get("opponent", "TBD"))
    team_goals = match.get("goals_for")
    opponent_goals = match.get("goals_against")
    selected_display = format_team_display(selected_team)
    opponent_display = format_team_display(opponent)

    if team_is_home:
        return f"{selected_display} {team_goals}-{opponent_goals} {opponent_display}"
    return f"{opponent_display} {opponent_goals}-{team_goals} {selected_display}"


def render_timeline_events(events: List[Dict[str, Any]], *, compact: bool = False) -> None:
    if not events:
        st.caption("No timeline events available.")
        return

    for event in events:
        minute = str(event.get("minute", "")).strip()
        label = str(event.get("label") or event.get("event_type") or "Event").strip()
        team = str(event.get("team") or "").strip()
        note = str(event.get("note") or "").strip()
        suffix = f" - {format_team_display(team)}" if team and team != "Match" else ""
        cols = st.columns([1, 6] if not compact else [1, 7])
        with cols[0]:
            st.markdown(f"**{minute}**")
        with cols[1]:
            st.markdown(f"**{label}{suffix}**")
            if note:
                st.caption(note)


def show_card(match: Dict[str, Any], key_prefix: str, editing_match_id: Any = None) -> None:
    stage = match.get("stage", "")
    locked = bool(match.get("locked", False))
    editable = bool(match.get("editable", False))
    status = "Locked" if locked else "Editable" if editable else "Fixed"
    stage_class = stage.lower() if stage else "default"
    extra_bits: List[str] = []
    if match.get("user_overridden"):
        extra_bits.append("User override")
    if match.get("extra_time"):
        extra_bits.append("AET")
    if match.get("penalties"):
        extra_bits.append(f"Pens {match.get('penalty_score', '')}")
    extra_html = " · ".join(extra_bits)

    home_display = format_team_display(match.get("home_team", "TBD"))
    away_display = format_team_display(match.get("away_team", "TBD"))

    st.markdown(
        f"""
        <div class="match-card">
            <div class="match-card-top">
                <div>
                    <span class="wc-chip wc-chip-{stage_class}">{stage_title(stage)}</span>
                    <span class="wc-chip wc-chip-status">{status}</span>
                </div>
                <div class="match-id">M{match.get('match_id')}</div>
            </div>
            <div class="match-teams">{home_display} vs {away_display}</div>
            <div class="match-score">{score_text(match)}</div>
            <div class="match-meta">{match_caption(match)}</div>
            <div class="match-meta muted">{extra_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cols = st.columns([1, 1, 1])
    with cols[0]:
        if editable and stage != "FINAL" and st.button("Edit", key=f"edit_{key_prefix}_{match.get('match_id')}", use_container_width=True):
            st.session_state["editing_match_id"] = match.get("match_id")
            st.session_state["editing_match"] = match
            st.rerun()

    if editing_match_id == match.get("match_id"):
        st.markdown("<div style='margin-top: 0.75rem;'></div>", unsafe_allow_html=True)
        render_match_editor(match)

    timeline = match.get("timeline") or []
    momentum_summary = str(match.get("momentum_summary") or "").strip()
    if timeline or momentum_summary:
        st.markdown("<div style='margin-top: 0.75rem; padding-top: 0.75rem; border-top: 1px solid rgba(255,255,255,0.1);'></div>", unsafe_allow_html=True)
        if momentum_summary:
            st.markdown(f"<div class='momentum-pill'>{momentum_summary}</div>", unsafe_allow_html=True)
        if timeline:
            st.caption("**Timeline**")
            render_timeline_events(timeline)


def render_match_editor(match: Dict[str, Any]) -> None:
    stage = match.get("stage", "")
    st.markdown("### Edit Match Override")
    st.caption(f"Match M{match.get('match_id')} · {stage_title(stage)}")

    with st.form(f"override_form_{match.get('match_id')}", clear_on_submit=False):
        score_cols = st.columns(2)
        with score_cols[0]:
            home_label = format_team_display(match.get("home_team"))
            home_score = st.number_input(
                f"{home_label} score",
                min_value=0,
                step=1,
                value=int(match.get("home_score") or 0),
            )
        with score_cols[1]:
            away_label = format_team_display(match.get("away_team"))
            away_score = st.number_input(
                f"{away_label} score",
                min_value=0,
                step=1,
                value=int(match.get("away_score") or 0),
            )

        penalties_winner: Optional[str] = None
        if stage != "GROUP" and home_score == away_score:
            penalties_winner = st.selectbox(
                "Penalty winner",
                ["home", "away"],
                format_func=lambda choice: match.get("home_team") if choice == "home" else match.get("away_team"),
            )

        submit_cols = st.columns(2)
        with submit_cols[0]:
            save_clicked = st.form_submit_button("Save override")
        with submit_cols[1]:
            cancel_clicked = st.form_submit_button("Cancel")

        if cancel_clicked:
            st.session_state.pop("editing_match_id", None)
            st.session_state.pop("editing_match", None)
            st.rerun()

        if save_clicked:
            payload = {
                "match_id": match.get("match_id"),
                "home_score": int(home_score),
                "away_score": int(away_score),
            }
            if penalties_winner:
                payload["penalties_winner"] = penalties_winner

            response = http_post("/api/v1/override_match", payload)
            if response.get("error"):
                st.error(response["error"])
            else:
                st.success("Tournament recalculated from overridden match.")
                st.session_state["tournament_state"] = normalize_state(response)
                st.session_state.pop("editing_match_id", None)
                st.session_state.pop("editing_match", None)
                st.rerun()


def render_stage_cards(matches: List[Dict[str, Any]], stage: str, editing_match_id: Any = None) -> None:
    stage_matches = [match for match in matches if match.get("stage") == stage]
    if not stage_matches:
        return

    st.markdown(f"#### {stage_title(stage)}")
    for index in range(0, len(stage_matches), 2):
        row = st.columns(2)
        for offset, column in enumerate(row):
            match_index = index + offset
            if match_index >= len(stage_matches):
                continue
            with column:
                show_card(stage_matches[match_index], f"{stage}_{match_index}", editing_match_id=editing_match_id)


def load_tournament_state(refresh: bool = False, simulations: Optional[int] = None) -> Dict[str, Any]:
    params = f"?refresh={'true' if refresh else 'false'}"
    if simulations is not None:
        params = f"{params}&simulations={simulations}"
    response = http_get(f"/api/v1/tournament_results{params}")
    return normalize_state(response)


def render_tournament_page() -> None:
    st.title("🏅 Tournament Simulation")
    st.caption("Run a full simulation, edit non-final matches, and resimulate from the affected stage onward.")

    action_cols = st.columns([1, 1, 3])
    with action_cols[0]:
        if st.button("Run Tournament Simulation", use_container_width=True):
            st.session_state["tournament_state"] = load_tournament_state(refresh=True, simulations=10)
            st.rerun()
    with action_cols[1]:
        if st.button("Refresh Saved State", use_container_width=True):
            st.session_state["tournament_state"] = load_tournament_state(refresh=False)
            st.rerun()

    state = st.session_state.get("tournament_state") or load_tournament_state(refresh=False)
    if not state:
        st.info("No tournament state available yet.")
        return

    matches = state.get("matches", [])
    matches.sort(key=lambda item: (stage_rank(item.get("stage", "")), item.get("match_id", 0)))

    summary_cols = st.columns(4)
    summary_cols[0].metric("Champion", state.get("champion", "TBD"))
    summary_cols[1].metric("Runner-up", state.get("runner_up", "TBD"))
    summary_cols[2].metric("Third Place", state.get("third_place", "TBD"))
    summary_cols[3].metric("Matches", len(matches))

    editing_id = st.session_state.get("editing_match_id")

    st.subheader("Group Stage Results")
    group_standings = state.get("group_standings", {})
    for group_name in sorted(group_standings.keys()):
        with st.expander(f"Group {group_name}", expanded=False):
            st.dataframe(display_data_frame(group_standings[group_name]), use_container_width=True, hide_index=True)

    st.subheader("Bracket")
    for stage in ["R32", "R16", "QF", "SF", "THIRD_PLACE", "FINAL"]:
        with st.expander(stage_title(stage), expanded=stage in {"SF", "FINAL"}):
            render_stage_cards(matches, stage, editing_match_id=editing_id)


def _available_play_as_teams() -> List[str]:
    state = st.session_state.get("tournament_state") or load_tournament_state(refresh=False)
    teams: set[str] = set()
    for match in state.get("matches", []):
        home = str(match.get("home_team", "")).strip()
        away = str(match.get("away_team", "")).strip()
        if home:
            teams.add(home)
        if away:
            teams.add(away)
    if teams:
        return sorted(teams)
    return TEAM_NAMES


def _play_as_result_badge(stage_reached: str) -> str:
    if stage_reached == "Champion":
        return "🏆 Champion"
    if stage_reached == "Runner-up":
        return "🥈 Runner-up"
    if stage_reached in {"Third Place", "Fourth Place"}:
        return f"🥉 {stage_reached}"
    return f"🎯 {stage_reached}"


def render_play_as_page() -> None:
    st.title("🎮 Play As A Team")
    st.caption("Simulate multiple tournaments for one selected team and view only that team's journey.")

    teams = _available_play_as_teams()
    default_team = "Argentina" if "Argentina" in teams else teams[0]

    controls = st.columns([2, 1, 1, 2])
    with controls[0]:
        selected_team = st.selectbox("Select Team", teams, index=teams.index(default_team))
    with controls[1]:
        simulations = st.number_input("Simulations", min_value=1, max_value=25, value=10, step=1, help="Number of tournament runs to aggregate for this selected team.")
    with controls[2]:
        st.empty()
    with controls[3]:
        simulate_clicked = st.button("Run Play As Simulations", use_container_width=True)

    if simulate_clicked:
        payload = {
            "team_name": selected_team,
            "simulations": int(simulations),
        }
        response = http_post("/api/v1/play_as", payload, timeout=240)
        if response.get("error"):
            st.error(f"Play As simulation failed: {response.get('error')}")
        else:
            st.session_state["play_as_result"] = normalize_state(response)

    result = st.session_state.get("play_as_result")
    if not result:
        st.info("Choose a team and run simulations to see tournament journeys.")
        return

    summary = result.get("summary", {})
    journeys = result.get("journeys", [])

    metrics = st.columns(6)
    metrics[0].metric("Titles Won", summary.get("titles_won", 0))
    with metrics[1]:
        st.markdown(
            f"""
            <div class="playas-stat">
                <div class="playas-stat-label">Average Finish</div>
                <div class="playas-stat-value">{summary.get('average_finish', 'N/A')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    metrics[2].metric("Goals Scored", summary.get("goals_scored", summary.get("average_goals_for", 0)))
    metrics[3].metric("Goals Conceded", summary.get("goals_conceded", summary.get("average_goals_against", 0)))
    metrics[4].metric("ET Frequency", f"{float(summary.get('et_frequency', 0.0)) * 100:.1f}%")
    metrics[5].metric("Pen Frequency", f"{float(summary.get('penalty_frequency', 0.0)) * 100:.1f}%")

    st.subheader("Elimination Distribution")
    elimination = summary.get("elimination_distribution", {})
    if elimination:
        dist_df = pd.DataFrame(
            [{"Stage": stage, "Count": count} for stage, count in elimination.items()]
        ).sort_values("Count", ascending=False)
        st.dataframe(dist_df, use_container_width=True, hide_index=True)
    else:
        st.caption("No elimination data available.")

    st.subheader("Simulation Journeys")
    for journey in journeys:
        sim_no = journey.get("simulation")
        stage_reached = str(journey.get("stage_reached", "Unknown"))
        title = f"Simulation {sim_no}: {_play_as_result_badge(stage_reached)}"
        with st.expander(title, expanded=sim_no == 1):
            momentum = str(journey.get("momentum_summary") or "").strip()
            if momentum:
                st.info(momentum)
            matches = journey.get("matches", [])
            for match in matches:
                stage_label = match.get("stage_label") or stage_title(str(match.get("stage", "")))
                et_pen = []
                if match.get("extra_time"):
                    et_pen.append("AET")
                if match.get("penalties"):
                    et_pen.append(f"Pens {match.get('penalty_score', '')}")
                suffix = f" {' | '.join(et_pen)}" if et_pen else ""
                st.markdown(f"**{stage_label}**")
                st.markdown(f"{format_journey_scoreline(match, selected_team)}")
                if suffix:
                    st.caption(suffix.strip())

                render_timeline_events(match.get("timeline") or [], compact=True)


def render_prediction_history() -> None:
    history_response = http_get("/api/v1/predictions/history?limit=5")
    history = history_response.get("data", []) if isinstance(history_response, dict) else []
    df = as_data_frame(history)
    if df.empty:
        st.info("No prediction history yet.")
        return

    display = pd.DataFrame(
        {
            "Time": df.get("timestamp", pd.Series(dtype=str)),
            "Match": df.get("match", pd.Series(dtype=str)),
            "Prediction": df.get("predicted_score", pd.Series(dtype=str)),
            "Confidence": df.get("confidence", pd.Series(dtype=float)),
            "Win %": df.get("home_win_pct", pd.Series(dtype=float)),
            "Draw %": df.get("draw_pct", pd.Series(dtype=float)),
            "Loss %": df.get("away_win_pct", pd.Series(dtype=float)),
        }
    )
    st.dataframe(display_data_frame(display), use_container_width=True, hide_index=True)


def render_predictions_page() -> None:
    st.title("🎯 Match Predictions")
    st.caption("Latest five predictions are stored automatically after every request.")

    col1, col2 = st.columns(2)
    with col1:
        home_team_name = st.selectbox("Home Team", TEAM_NAMES, index=0)
    with col2:
        away_team_name = st.selectbox("Away Team", TEAM_NAMES, index=3)

    if st.button("Generate Prediction"):
        payload = {"home_team_id": TEAMS[home_team_name], "away_team_id": TEAMS[away_team_name]}
        response = http_post("/api/v1/predictions/predict", payload)
        if response.get("error"):
            st.error(f"Prediction failed: {response.get('error')}")
        else:
            result_cols = st.columns(4)
            result_cols[0].metric("Home Win", f"{response.get('home_win_pct', 0)}%")
            result_cols[1].metric("Draw", f"{response.get('draw_pct', 0)}%")
            result_cols[2].metric("Away Win", f"{response.get('away_win_pct', 0)}%")
            result_cols[3].metric("Confidence", f"{response.get('confidence', 0)}%")
            st.success(f"Prediction: {response.get('match')} → {response.get('predicted_score')}")
            if response.get("explanation"):
                st.caption(response.get("explanation"))

    st.divider()
    st.subheader("Prediction History")
    render_prediction_history()


def render_rankings_page() -> None:
    st.title("🏆 Global Rankings")
    conf = st.selectbox("Confederation", ["All", "UEFA", "CONMEBOL", "CONCACAF", "CAF", "AFC", "OFC"], index=0)
    limit = st.slider("Show top", 8, 64, 16)
    query = f"/api/v1/countries/rankings?confederation={'' if conf == 'All' else conf}&limit={limit}"
    response = http_get(query)
    if response.get("error"):
        st.info("Backend rankings not available — showing sample")
        sample = pd.DataFrame({"Rank": [1, 2, 3, 4, 5], "Team": ["Spain", "Brazil", "Argentina", "France", "Germany"], "ELO": [1850, 1820, 1800, 1790, 1760]})
        st.dataframe(display_data_frame(sample), use_container_width=True, hide_index=True)
        return
    st.dataframe(display_data_frame(response.get("data", [])), use_container_width=True, hide_index=True)


def render_analytics_page() -> None:
    st.title("📈 Team Analytics")
    team_name = st.selectbox("Select Team", TEAM_NAMES, index=0)
    if st.button("Fetch Analytics"):
        response = http_get(f"/api/v1/analytics/team/{TEAMS[team_name]}")
        if response.get("error"):
            st.error(f"Analytics unavailable: {response.get('error')}")
        else:
            st.json(response)


def render_dashboard_page() -> None:
    st.title("📊 Dashboard")
    cols = st.columns(4)
    cols[0].metric("Teams", "48")
    cols[1].metric("Matches", "104")
    cols[2].metric("Host Nations", "3")
    cols[3].metric("Simulations", "200+")

    st.divider()
    st.subheader("System Status")
    health = http_get("/api/v1/health")
    if health.get("error"):
        st.error(f"Backend unreachable: {health.get('error')}")
    else:
        st.success("Backend API: Connected")
        st.json(health)

    st.divider()
    st.subheader("Recent Predictions")
    recent = http_get("/api/v1/predictions/upcoming")
    if recent.get("error"):
        st.info("No recent predictions from backend — showing sample data")
        sample = pd.DataFrame({"Match": ["Spain vs Germany", "Brazil vs Argentina", "France vs England"], "Home Win": ["62%", "48%", "52%"], "Draw": ["18%", "22%", "20%"], "Away Win": ["20%", "30%", "28%"]})
        st.dataframe(sample, use_container_width=True, hide_index=True)
    else:
        st.dataframe(as_data_frame(recent.get("data", [])), use_container_width=True, hide_index=True)


st.markdown(
    """
    <style>
        [data-testid="stMainBlockContainer"] { padding: 2rem; }
        .block-container { max-width: 1220px; }
        h1, h2, h3 { letter-spacing: 0.01em; }
        .match-card {
            background: linear-gradient(180deg, #1a1f25 0%, #171b20 100%);
            border: 1px solid #343b45;
            border-radius: 0.95rem;
            padding: 1rem 1rem 0.95rem 1rem;
            margin-bottom: 0.95rem;
            box-shadow: 0 10px 26px rgba(0, 0, 0, 0.22);
        }
        .match-card-top {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.72rem;
        }
        .match-id { color: #91a4c2; font-size: 0.82rem; }
        .match-teams { color: #eef2f7; font-size: 1.02rem; font-weight: 650; margin-bottom: 0.35rem; }
        .match-score { color: #89e9a3; font-size: 1.5rem; font-weight: 760; margin-bottom: 0.32rem; letter-spacing: 0.01em; }
        .match-meta { color: #b6c1d3; font-size: 0.86rem; }
        .match-meta.muted { color: #8a96aa; }
        .momentum-pill {
            border: 1px solid #30485b;
            background: #1a2733;
            color: #d8ecff;
            border-radius: 0.7rem;
            padding: 0.56rem 0.68rem;
            font-size: 0.85rem;
            margin-bottom: 0.6rem;
        }
        .timeline-row {
            display: grid;
            grid-template-columns: 72px 1fr;
            gap: 0.55rem;
            border-bottom: 1px solid #2a2f35;
            padding: 0.42rem 0;
        }
        .timeline-row.compact {
            grid-template-columns: 66px 1fr;
            padding: 0.32rem 0;
        }
        .timeline-minute {
            color: #9eb2cc;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.02em;
        }
        .timeline-label {
            color: #ecf3ff;
            font-size: 0.88rem;
            line-height: 1.25rem;
            font-weight: 530;
        }
        .timeline-note {
            color: #97a8bc;
            font-size: 0.78rem;
            margin-top: 0.12rem;
        }
        .playas-stat {
            border-radius: 0.8rem;
            border: 1px solid #303844;
            background: #171d25;
            padding: 0.75rem 0.85rem 0.68rem 0.85rem;
            min-height: 100%;
        }
        .playas-stat-label {
            color: #d2dae6;
            font-size: 0.82rem;
            margin-bottom: 0.35rem;
        }
        .playas-stat-value {
            color: #f3f6fb;
            font-size: 1.5rem;
            line-height: 1.1;
            font-weight: 650;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .journey-card {
            border: 1px solid #313a45;
            border-radius: 0.8rem;
            padding: 0.58rem 0.72rem;
            margin-top: 0.55rem;
            margin-bottom: 0.2rem;
            background: #171d25;
        }
        .journey-head {
            display: flex;
            justify-content: space-between;
            gap: 0.6rem;
            align-items: baseline;
        }
        .journey-stage {
            color: #eef4ff;
            font-weight: 650;
            font-size: 0.9rem;
        }
        .journey-score {
            color: #8fe3a5;
            font-weight: 730;
            font-size: 0.95rem;
        }
        .journey-meta {
            color: #9fb0c8;
            font-size: 0.79rem;
            margin-top: 0.14rem;
        }
        .wc-chip {
            display: inline-block;
            padding: 0.2rem 0.55rem;
            border-radius: 999px;
            font-size: 0.72rem;
            letter-spacing: 0.02em;
            margin-right: 0.35rem;
            border: 1px solid rgba(255,255,255,0.09);
        }
        .wc-chip-status { background: #252b33; color: #d1d8e3; }
        .wc-chip-group { background: #223044; color: #d8e6ff; }
        .wc-chip-r32 { background: #1f3147; color: #d8e6ff; }
        .wc-chip-r16 { background: #1f3640; color: #d7f0ee; }
        .wc-chip-qf { background: #2f3046; color: #e0dfff; }
        .wc-chip-sf { background: #3a2f46; color: #f2defc; }
        .wc-chip-third_place { background: #42352c; color: #f1e2d6; }
        .wc-chip-final { background: #433127; color: #f5e6d4; }
        @media (max-width: 960px) {
            [data-testid="stMainBlockContainer"] { padding: 1rem; }
            .timeline-row, .timeline-row.compact {
                grid-template-columns: 56px 1fr;
            }
            .match-score { font-size: 1.3rem; }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


st.sidebar.title("⚽ WC26 INTEL™")
page = st.sidebar.radio("Navigate", ["Dashboard", "Predictions", "Rankings", "Analytics", "Tournament", "Play As A Team"])

if page == "Dashboard":
    render_dashboard_page()
elif page == "Predictions":
    render_predictions_page()
elif page == "Rankings":
    render_rankings_page()
elif page == "Analytics":
    render_analytics_page()
elif page == "Tournament":
    render_tournament_page()
elif page == "Play As A Team":
    render_play_as_page()

st.divider()
st.caption("WC26 Intelligence Platform | Backend: Online | Status: Ready")