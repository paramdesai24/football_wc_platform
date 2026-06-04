"""
Attack & Defense Rating 2.0

Multi-component football-intelligence model replacing the percentile-based
attack_rating / defense_rating.

Components:
  A (40%) - Recency-weighted goals vs. Elo-adjusted opponents (730-day half-life)
  B (25%) - Squad quality (attackers/defenders/GK, 2025-26 active players)
  C (20%) - Elo min-max normalization
  D (15%) - Recent form score

Output files (parallel, do NOT overwrite production):
  processed/attack_defense_ratings_v2_comparison.csv
  processed/attack_defense_v2_components.csv
  processed/attack_breakdown.json
  processed/defense_breakdown.json
  processed/component_distribution.csv
  processed/correlation_matrix.csv
"""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy.stats import norm as scipy_norm

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────────────────────────────────────

PROCESSED_DIR = Path(r"C:\FIFA WC\platform\data\processed")
FBREF_PATH = Path(r"C:\FIFA WC\DATA\latest\players_data_light-2025_2026.csv")

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

HALF_LIFE_DAYS: float = 730.0       # 2-year half-life for international football
ELO_BASELINE: float = 1500.0        # neutral reference Elo
DECAY_LAMBDA: float = math.log(2) / HALF_LIFE_DAYS

# Weights must sum to 1.0
ATTACK_WEIGHTS = dict(recency=0.40, squad=0.25, elo=0.20, form=0.15)
DEFENSE_WEIGHTS = dict(recency=0.40, squad=0.25, elo=0.20, form=0.15)

# Active player filter for master_players (eliminates retired/inactive)
MIN_MARKET_VALUE = 1.0    # exclude 0-value (typically retired/unknown)
MIN_ACTIVE_SCORE = 0.0    # form_score OR goals_per_90 must be > 0

# Squad depth per country
TOP_ATTACKERS = 15
TOP_DEFENDERS = 8

# ─────────────────────────────────────────────────────────────────────────────
# FIFA ISO3 → system country_uid
# Source: FBRef uses FIFA 3-letter codes; our system uses custom UIDs.
# ─────────────────────────────────────────────────────────────────────────────

_ISO3_TO_UID: dict[str, str] = {
    # Europe
    "ALB": "C_AL",     "ALG": "C_DZ",     "ARM": "C_AM",     "AUT": "C_AT",
    "BEL": "C_BE",     "BIH": "C_BA",     "BUL": "C_BG",     "BYE": "C_BY",
    "CRO": "C_HR",     "CYP": "C_CY",     "CZE": "C_CZ",     "DEN": "C_DK",
    "ENG": "C_GB-ENG", "ESP": "C_ES",     "EST": "C_EE",     "FIN": "C_FI",
    "FRA": "C_FR",     "GEO": "C_GE",     "GER": "C_DE",     "GRE": "C_GR",
    "HUN": "C_HU",     "IRL": "C_IE",     "ISL": "C_IS",     "ITA": "C_IT",
    "KVX": "C_XK",     "LTU": "C_LT",     "LUX": "C_LU",     "LVA": "C_LV",
    "MKD": "C_MK",     "MLT": "C_MT",     "MNE": "C_ME",     "NED": "C_NL",
    "NIR": "C_GB-NIR", "NOR": "C_NO",     "POL": "C_PL",     "POR": "C_PT",
    "ROU": "C_RO",     "RUS": "C_RU",     "SCO": "C_GB-SCT", "SRB": "C_RS",
    "SUI": "C_CH",     "SVK": "C_SK",     "SVN": "C_SI",     "SWE": "C_SE",
    "TUR": "C_TR",     "UKR": "C_UA",     "WAL": "C_GB-WLS",
    # South America
    "ARG": "C_AR",     "BOL": "C_BO",     "BRA": "C_BR",     "CHI": "C_CL",
    "COL": "C_CO",     "ECU": "C_EC",     "PAR": "C_PY",     "PER": "C_PE",
    "URU": "C_UY",     "VEN": "C_VE",     "SUR": "C_SR",
    # CONCACAF
    "CAN": "C_CA",     "CRC": "C_CR",     "CUB": "C_CU",     "CUR": "C_CW",
    "DOM": "C_DO",     "GUA": "C_GT",     "HAI": "C_HT",     "HON": "C_HN",
    "JAM": "C_JM",     "MEX": "C_MX",     "NCA": "C_NI",     "PAN": "C_PA",
    "SLV": "C_SV",     "TRI": "C_TT",     "USA": "C_US",
    # Africa
    "ANG": "C_AO",     "BEN": "C_BJ",     "BFA": "C_BF",     "CMR": "C_CM",
    "CIV": "C_CI",     "COD": "C_CD",     "CPV": "C_CV",     "EGY": "C_EG",
    "EQG": "C_GQ",     "GAB": "C_GA",     "GAM": "C_GM",     "GHA": "C_GH",
    "GNB": "C_GW",     "GUI": "C_GN",     "KEN": "C_KE",     "LBY": "C_LY",
    "MAR": "C_MA",     "MLI": "C_ML",     "MOZ": "C_MZ",     "MTN": "C_MR",
    "NAM": "C_NA",     "NGA": "C_NG",     "RSA": "C_ZA",     "SEN": "C_SN",
    "TAN": "C_TZ",     "TOG": "C_TG",     "TUN": "C_TN",     "UGA": "C_UG",
    "ZAM": "C_ZM",     "ZIM": "C_ZW",
    # Asia / Middle East
    "AUS": "C_AU",     "BHR": "C_BH",     "CHN": "C_CN",     "IDN": "C_ID",
    "IND": "C_IN",     "IRN": "C_IR",     "IRQ": "C_IQ",     "ISR": "C_ISR",
    "JOR": "C_JO",     "JPN": "C_JP",     "KAZ": "C_KZ",     "KGZ": "C_KG",
    "KOR": "C_KR",     "KSA": "C_SA",     "KWT": "C_KW",     "LBN": "C_LB",
    "NZL": "C_NZ",     "OMA": "C_OM",     "PRK": "C_KP",     "PSE": "C_PS",
    "QAT": "C_QA",     "SYR": "C_SY",     "THA": "C_TH",     "TJK": "C_TJ",
    "UAE": "C_AE",     "UZB": "C_UZ",     "VIE": "C_VN",
    # Oceania / Other
    "FIJ": "C_FJ",     "NCL": "C_NC",     "SOL": "C_SB",     "TAH": "C_PF",
    # Alternative ISO3 codes used by FBRef (some non-standard)
    "GUF": None,   # French Guiana — not in our system
    "MTQ": None,   # Martinique — not in our system
    "GLP": None,   # Guadeloupe — not in our system
    "CTA": None,   # Central African Republic — not in our system
    "BDI": None,   # Burundi — not in our system
}


def iso3_to_uid(iso3: str) -> Optional[str]:
    """Convert FBRef FIFA ISO3 code to system country_uid. Returns None if unknown."""
    return _ISO3_TO_UID.get(iso3.upper())


# ─────────────────────────────────────────────────────────────────────────────
# Utility functions
# ─────────────────────────────────────────────────────────────────────────────

def _minmax(series: pd.Series, clip_percentile: float = 99.0) -> pd.Series:
    """Min-max normalize a series. Clips at clip_percentile to reduce outlier impact."""
    cap = series.quantile(clip_percentile / 100.0)
    clipped = series.clip(upper=cap)
    lo, hi = clipped.min(), clipped.max()
    if hi == lo:
        return pd.Series(0.5, index=series.index)
    return (clipped - lo) / (hi - lo)


def _decay_weight(days_since: float) -> float:
    """Exponential decay weight. Returns 1.0 for today, 0.5 at HALF_LIFE_DAYS."""
    return math.exp(-DECAY_LAMBDA * max(days_since, 0.0))


def _percentile_rank(series: pd.Series) -> pd.Series:
    """Convert values to percentile rank [0, 100] — for display only."""
    return series.rank(method="average", pct=True) * 100


def _compute_clean_sheet_scores_A(fbref_df: pd.DataFrame) -> dict[str, float]:
    """
    Compute clean-sheet score per nation from FBRef GK data for Component A.
    """
    df = fbref_df.copy()
    df["iso3"] = df["Nation"].str.extract(r"([A-Z]{3})$")
    gk = df[(df["Pos"] == "GK") & df["GA"].notna() & df["CS%"].notna()].copy()

    scores: dict[str, float] = {}
    for iso3, grp in gk.groupby("iso3"):
        uid = _ISO3_TO_UID.get(str(iso3).upper())
        if uid is None:
            continue
        starter = grp.nlargest(1, "Min").iloc[0]
        cs_pct  = float(starter.get("CS%", 0) or 0) / 100.0
        ga90    = float(starter.get("GA90", 3.0) or 3.0)
        scores[uid] = 0.60 * cs_pct + 0.40 * max(0.0, 1.0 - ga90 / 3.0)

    return scores


def normalize_zscore_cdf(raw: pd.Series) -> pd.Series:
    """
    Z-score CDF normalization. Lower raw = better defense -> higher score.
    """
    mu  = raw.mean()
    sig = raw.std()
    if sig == 0:
        return pd.Series(50.0, index=raw.index)
    z = (raw - mu) / sig
    return 100.0 * (1.0 - scipy_norm.cdf(z))


# ─────────────────────────────────────────────────────────────────────────────
# Data loaders
# ─────────────────────────────────────────────────────────────────────────────

def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load all required datasets.

    Returns:
        rankings_df      — dynamic_world_rankings_active.csv (all countries)
        results_df       — historical_results_mapped.csv (all international matches)
        master_players   — master_players.csv (squad data, will be filtered)
        fbref_df         — players_data_light-2025_2026.csv (active-season player stats)

    Elo strategy:
        dynamic_world_rankings_active.csv has has_elo=False for some teams (e.g. Morocco).
        We supplement with elo_rankings_active.csv which has proper Elo for all teams.
    """
    rankings_df = pd.read_csv(PROCESSED_DIR / "dynamic_world_rankings_active.csv")

    # Patch Elo: elo_rankings_active has accurate Elo for all teams
    try:
        elo_src = pd.read_csv(PROCESSED_DIR / "elo_rankings_active.csv")[["country_uid", "elo_rating"]]
        elo_src = elo_src.rename(columns={"elo_rating": "elo_from_src"})
        rankings_df = rankings_df.merge(elo_src, on="country_uid", how="left")
        # Use elo_from_src where existing elo_rating is baseline (1500) or has_elo=False
        mask = (rankings_df["has_elo"] == False) | (rankings_df["elo_rating"] <= ELO_BASELINE)
        rankings_df.loc[mask, "elo_rating"] = rankings_df.loc[mask, "elo_from_src"].fillna(ELO_BASELINE)
        rankings_df = rankings_df.drop(columns=["elo_from_src"])
        patched = mask.sum()
        logger.info(f"Elo patch: corrected {patched} teams using elo_rankings_active.csv")
    except Exception as e:
        logger.warning(f"Could not patch Elo from elo_rankings_active: {e}")

    results_df = pd.read_csv(PROCESSED_DIR / "historical_results_mapped.csv")
    master_players = pd.read_csv(PROCESSED_DIR / "master_players.csv")
    fbref_df = pd.read_csv(FBREF_PATH)
    logger.info(
        f"Loaded inputs: rankings={len(rankings_df)}, "
        f"results={len(results_df)}, players={len(master_players)}, "
        f"fbref={len(fbref_df)}"
    )
    return rankings_df, results_df, master_players, fbref_df


# ─────────────────────────────────────────────────────────────────────────────
# Component A — Recency-weighted goals (attack & defense)
# ─────────────────────────────────────────────────────────────────────────────

def compute_component_a(
    results_df: pd.DataFrame,
    elo_lookup: dict[str, float],
    eligible_uids: set[str],
    name_to_uid: dict[str, str],
) -> dict[str, dict[str, float]]:
    """
    Vectorized computation of recency-weighted, Elo-adjusted goals per match.

    Matching strategy:
      1. Name-based: map home_team/away_team text → uid via name_to_uid (128/130 coverage)
      2. UID-based fallback: use home_country_uid/away_country_uid columns as supplement

    Opponent adjustment:
      opp_factor = opponent_elo / ELO_BASELINE
      Attack:  goals_scored  * opp_factor  (goals vs strong teams count more)
      Defense: goals_conceded / opp_factor (conceding to Spain hurts less)
    """
    today_ts = pd.Timestamp.now(tz="UTC")

    df = results_df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce", utc=True)
    df = df.dropna(subset=["date", "home_team", "away_team", "home_score", "away_score"])

    # ── Name-based UID mapping (primary — covers 128/130 eligible teams) ──
    df["home_uid"] = df["home_team"].str.strip().str.lower().map(name_to_uid)
    df["away_uid"] = df["away_team"].str.strip().str.lower().map(name_to_uid)

    # ── UID fallback: for rows where name mapping missed, try legacy UID cols ──
    if "home_country_uid" in df.columns:
        mask_h = df["home_uid"].isna() & df["home_country_uid"].isin(eligible_uids)
        df.loc[mask_h, "home_uid"] = df.loc[mask_h, "home_country_uid"]
    if "away_country_uid" in df.columns:
        mask_a = df["away_uid"].isna() & df["away_country_uid"].isin(eligible_uids)
        df.loc[mask_a, "away_uid"] = df.loc[mask_a, "away_country_uid"]

    # Drop rows where both teams are unmapped (not eligible)
    df = df.dropna(subset=["home_uid", "away_uid"], how="all")

    # Decay weight — fully vectorised with numpy
    days_since = (today_ts - df["date"]).dt.days.clip(lower=0).astype(float)
    df["w"] = np.exp(-DECAY_LAMBDA * days_since)

    # Elo of each team in the match (use uid-based lookup)
    df["home_elo"] = df["home_uid"].map(elo_lookup).fillna(
        df["home_team"].str.strip().str.lower().map(
            {k: elo_lookup.get(v, ELO_BASELINE) for k, v in name_to_uid.items()}
        )
    ).fillna(ELO_BASELINE)
    df["away_elo"] = df["away_uid"].map(elo_lookup).fillna(
        df["away_team"].str.strip().str.lower().map(
            {k: elo_lookup.get(v, ELO_BASELINE) for k, v in name_to_uid.items()}
        )
    ).fillna(ELO_BASELINE)

    df["home_opp_f"] = df["away_elo"] / ELO_BASELINE
    df["away_opp_f"] = df["home_elo"] / ELO_BASELINE

    # Weighted Elo-adjusted goals
    df["w_home_scored"]   = df["w"] * df["home_score"].astype(float) * df["home_opp_f"]
    df["w_home_conceded"] = df["w"] * df["away_score"].astype(float) / df["home_opp_f"]
    df["w_away_scored"]   = df["w"] * df["away_score"].astype(float) * df["away_opp_f"]
    df["w_away_conceded"] = df["w"] * df["home_score"].astype(float) / df["away_opp_f"]

    # Aggregate per team (home + away combined)
    home_df = df.dropna(subset=["home_uid"])
    away_df  = df.dropna(subset=["away_uid"])

    home_agg = home_df.groupby("home_uid")[["w", "w_home_scored", "w_home_conceded"]].sum()
    home_agg.columns = ["wt", "scored", "conceded"]

    away_agg = away_df.groupby("away_uid")[["w", "w_away_scored", "w_away_conceded"]].sum()
    away_agg.columns = ["wt", "scored", "conceded"]

    combined = home_agg.add(away_agg, fill_value=0.0)
    covered = len([u for u in eligible_uids if u in combined.index])
    logger.info(f"Component A: name-matched {covered}/{len(eligible_uids)} eligible teams")

    out: dict[str, dict[str, float]] = {}
    for uid in eligible_uids:
        if uid in combined.index:
            row = combined.loc[uid]
            wt = float(row["wt"])
            if wt > 0:
                out[uid] = {
                    "attack_raw_A":  float(row["scored"])   / wt,
                    "defense_raw_A": float(row["conceded"]) / wt,
                    "match_weight":  wt,
                }
            else:
                logger.warning(f"Component A: zero weight for {uid}")
                out[uid] = {"attack_raw_A": 0.0, "defense_raw_A": 999.0, "match_weight": 0.0}
        else:
            logger.warning(f"Component A: no match data for {uid}")
            out[uid] = {"attack_raw_A": 0.0, "defense_raw_A": 999.0, "match_weight": 0.0}

    return out


# ─────────────────────────────────────────────────────────────────────────────
# Component B — Squad quality (active players only)
# ─────────────────────────────────────────────────────────────────────────────

def _filter_active_players(master_players: pd.DataFrame) -> pd.DataFrame:
    """
    Remove retired and inactive players from master_players.
    Active = market_value > 0 AND (form_score > 0 OR goals_per_90 > 0 OR assists_per_90 > 0)
    """
    mp = master_players.copy()
    active = (
        (mp["market_value"] > MIN_MARKET_VALUE) &
        (
            (mp["form_score"] > 0) |
            (mp["goals_per_90"] > 0) |
            (mp["assists_per_90"] > 0)
        )
    )
    filtered = mp[active].copy()
    removed = len(mp) - len(filtered)
    logger.info(f"Active player filter: kept {len(filtered)}/{len(mp)} (removed {removed} inactive/retired)")
    return filtered


def _global_norms(players: pd.DataFrame) -> dict[str, float]:
    """
    Compute global normalization caps (99th percentile) for player metrics.
    These are computed once across ALL active players to ensure consistent scaling.
    """
    return {
        "mv_cap":   players["market_value"].quantile(0.99),
        "ga_cap":   (players["goals_per_90"] + players["assists_per_90"]).quantile(0.99),
        "form_cap": players["form_score"].quantile(0.99),
    }


def compute_component_b_attack(
    master_players: pd.DataFrame,
    uid_to_name: dict[str, str],
    name_to_uid: dict[str, str],
) -> dict[str, float]:
    """
    Squad attack quality per country_uid.

    Formula per player:
        player_attack_score = 0.45 * mv_norm + 0.35 * ga_per_90_norm + 0.20 * form_norm
    Average over top-15 players by market_value (ATTACK + MIDFIELD).
    """
    active = _filter_active_players(master_players)
    attack_mid = active[active["position"].isin(["ATTACK", "MIDFIELD"])].copy()
    caps = _global_norms(active)

    # Pre-compute GA per90 column
    attack_mid["ga_per_90"] = attack_mid["goals_per_90"] + attack_mid["assists_per_90"]

    out: dict[str, float] = {}

    # Map country_of_citizenship → country_uid
    for country_name, group in attack_mid.groupby("country_of_citizenship"):
        uid = name_to_uid.get(str(country_name).strip().lower())
        if uid is None:
            continue  # not prediction-eligible

        top = group.nlargest(TOP_ATTACKERS, "market_value")
        if top.empty:
            continue

        mv_norm = (top["market_value"].clip(upper=caps["mv_cap"]) / caps["mv_cap"]).clip(0, 1)
        ga_norm = (top["ga_per_90"].clip(upper=caps["ga_cap"]) / caps["ga_cap"]).clip(0, 1)
        form_norm = (top["form_score"].clip(upper=caps["form_cap"]) / caps["form_cap"]).clip(0, 1)

        score = 0.45 * mv_norm + 0.35 * ga_norm + 0.20 * form_norm
        out[uid] = float(score.mean())

    logger.info(f"Component B (attack): computed for {len(out)} countries")
    return out


def _compute_gk_scores_fbref(fbref_df: pd.DataFrame) -> dict[str, float]:
    """
    Extract GK quality scores from FBRef 2025/26 season data.
    Starter GK = most minutes played per nation.

    gk_score = 0.5*(Save%/100) + 0.3*(CS%/100) + 0.2*max(0, 1 - GA90/3)
    """
    df = fbref_df.copy()
    df["iso3"] = df["Nation"].str.extract(r"([A-Z]{3})$")
    gk = df[(df["Pos"] == "GK") & df["GA"].notna() & df["Save%"].notna()].copy()

    gk_scores: dict[str, float] = {}
    for iso3, group in gk.groupby("iso3"):
        uid = iso3_to_uid(str(iso3))
        if uid is None:
            continue
        starter = group.nlargest(1, "Min").iloc[0]
        save_pct = float(starter.get("Save%", 0) or 0) / 100.0
        cs_pct = float(starter.get("CS%", 0) or 0) / 100.0
        ga90 = float(starter.get("GA90", 3) or 3)
        gk_score = 0.5 * save_pct + 0.3 * cs_pct + 0.2 * max(0.0, 1.0 - ga90 / 3.0)
        gk_scores[uid] = gk_score

    logger.info(f"FBRef GK scores computed for {len(gk_scores)} nations")
    return gk_scores


def _compute_gk_scores_fallback(
    master_players: pd.DataFrame,
    name_to_uid: dict[str, str],
    caps: dict[str, float],
) -> dict[str, float]:
    """Fallback GK score from master_players when FBRef data is absent."""
    active = _filter_active_players(master_players)
    gk_players = active[active["position"] == "GOALKEEPER"].copy()
    out: dict[str, float] = {}
    for country_name, group in gk_players.groupby("country_of_citizenship"):
        uid = name_to_uid.get(str(country_name).strip().lower())
        if uid is None:
            continue
        top = group.nlargest(2, "market_value")
        if top.empty:
            continue
        mv_norm = (top["market_value"].clip(upper=caps["mv_cap"]) / caps["mv_cap"]).clip(0, 1)
        form_norm = (top["form_score"].clip(upper=caps["form_cap"]) / caps["form_cap"]).clip(0, 1)
        # Normalize GK to same 0-1 scale as FBRef gk_score (which maxes ~0.8-0.9)
        raw = (0.70 * mv_norm + 0.30 * form_norm).mean()
        out[uid] = float(raw) * 0.85  # slight discount for lower-quality data
    return out


def compute_component_b_defense(
    master_players: pd.DataFrame,
    fbref_df: pd.DataFrame,
    uid_to_name: dict[str, str],
    name_to_uid: dict[str, str],
) -> dict[str, float]:
    """
    Squad defense quality per country_uid.

    defender_score = 0.70 * mv_norm + 0.30 * form_norm  (top-8 defenders)
    gk_score = FBRef 2025/26 (or master_players fallback)
    squad_defense_B = 0.70 * defender_score + 0.30 * gk_score
    """
    active = _filter_active_players(master_players)
    defenders = active[active["position"] == "DEFENDER"].copy()
    caps = _global_norms(active)

    # GK scores: FBRef primary, fallback for rest
    fbref_gk = _compute_gk_scores_fbref(fbref_df)
    fallback_gk = _compute_gk_scores_fallback(master_players, name_to_uid, caps)

    out: dict[str, float] = {}

    for country_name, group in defenders.groupby("country_of_citizenship"):
        uid = name_to_uid.get(str(country_name).strip().lower())
        if uid is None:
            continue

        top = group.nlargest(TOP_DEFENDERS, "market_value")
        if top.empty:
            defender_score = 0.0
        else:
            mv_norm = (top["market_value"].clip(upper=caps["mv_cap"]) / caps["mv_cap"]).clip(0, 1)
            form_norm = (top["form_score"].clip(upper=caps["form_cap"]) / caps["form_cap"]).clip(0, 1)
            defender_score = float((0.70 * mv_norm + 0.30 * form_norm).mean())

        gk_score = fbref_gk.get(uid) or fallback_gk.get(uid, 0.0)

        out[uid] = 0.70 * defender_score + 0.30 * gk_score

    logger.info(f"Component B (defense): computed for {len(out)} countries")
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Main computation
# ─────────────────────────────────────────────────────────────────────────────

def compute_v2_ratings(
    rankings_df: pd.DataFrame,
    results_df: pd.DataFrame,
    master_players: pd.DataFrame,
    fbref_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute attack_rating_v2 and defense_rating_v2 for all prediction_eligible teams.

    Returns a DataFrame with all components and final ratings.
    """
    eligible = rankings_df[rankings_df["prediction_eligible"] == True].copy()
    eligible_uids = set(eligible["country_uid"].tolist())

    logger.info(f"Computing v2 ratings for {len(eligible_uids)} prediction-eligible teams")

    # Build uid ↔ name lookup (lower-cased country_name → uid)
    uid_to_name: dict[str, str] = dict(zip(eligible["country_uid"], eligible["country_name"]))
    name_to_uid: dict[str, str] = {
        v.strip().lower(): k
        for k, v in uid_to_name.items()
    }

    # Build Elo lookup for opponent adjustment
    elo_lookup: dict[str, float] = dict(
        zip(rankings_df["country_uid"].astype(str), rankings_df["elo_rating"].fillna(ELO_BASELINE))
    )

    # ── Component A ──────────────────────────────────────────────────────────
    logger.info("Computing Component A: recency-weighted goals...")
    comp_a = compute_component_a(results_df, elo_lookup, eligible_uids, name_to_uid)

    # ── Component B ──────────────────────────────────────────────────────────
    logger.info("Computing Component B: squad quality...")
    comp_b_attack = compute_component_b_attack(master_players, uid_to_name, name_to_uid)
    comp_b_defense = compute_component_b_defense(master_players, fbref_df, uid_to_name, name_to_uid)

    # ── Assemble raw values ──────────────────────────────────────────────────
    rows = []
    for _, row in eligible.iterrows():
        uid = row["country_uid"]
        a = comp_a.get(uid, {"attack_raw_A": 0.0, "defense_raw_A": 999.0, "match_weight": 0.0})
        rows.append({
            "country_uid":             uid,
            "country_name":            row["country_name"],
            "elo_rating":              float(row.get("elo_rating", ELO_BASELINE) or ELO_BASELINE),
            "recent_form_D":           float(row.get("recent_form_score", 0.5) or 0.5),
            "squad_overall_strength":  float(row.get("squad_overall_strength", 0.5) or 0.5),
            "attack_v1":               float(row.get("attack_rating", 0) or 0),
            "defense_v1":              float(row.get("defense_rating", 0) or 0),
            "attack_raw_A":            a["attack_raw_A"],
            "defense_raw_A":           a["defense_raw_A"],   # lower = better
            "squad_attack_B":          comp_b_attack.get(uid, float("nan")),
            "squad_defense_B":         comp_b_defense.get(uid, float("nan")),
            "match_weight":            a["match_weight"],
        })

    df = pd.DataFrame(rows)

    # Fill missing squad B scores with population median (prediction-eligible subset)
    atk_b_median = df["squad_attack_B"].median()
    def_b_median = df["squad_defense_B"].median()
    n_missing_atk = df["squad_attack_B"].isna().sum()
    n_missing_def = df["squad_defense_B"].isna().sum()
    if n_missing_atk:
        logger.warning(f"Component B attack: {n_missing_atk} countries missing — filling with median")
    if n_missing_def:
        logger.warning(f"Component B defense: {n_missing_def} countries missing — filling with median")
    df["squad_attack_B"] = df["squad_attack_B"].fillna(atk_b_median)
    df["squad_defense_B"] = df["squad_defense_B"].fillna(def_b_median)

    # ── Min-max normalize each component ─────────────────────────────────────
    logger.info("Applying min-max normalization per component...")

    # Component A Attack: higher goals scored = better attack
    df["A_attack_norm"] = _minmax(df["attack_raw_A"])

    # ── Component A Defense (V2.1 Z-score CDF with 99% Outlier Clipping and 70/30 GK Clean Sheet Blend) ──
    cs_scores = _compute_clean_sheet_scores_A(fbref_df)
    
    # 1. Clip raw concession rating at 99th percentile to remove sentinel (999.0) outlier impact
    cap = float(df["defense_raw_A"].quantile(0.99))
    clipped_raw = df["defense_raw_A"].clip(upper=cap)
    
    # 2. Rescale raw conceded equivalent to [0, 1] where 0 = worst (concedes most) and 1 = best
    raw_min, raw_max = clipped_raw.min(), clipped_raw.max()
    if raw_max > raw_min:
        inv_raw_01 = 1.0 - (clipped_raw - raw_min) / (raw_max - raw_min)
    else:
        inv_raw_01 = pd.Series(0.5, index=df.index)
        
    # 3. Impute clean sheet scores (median imputation for neutral treatment)
    cs_median = float(pd.Series(list(cs_scores.values())).median()) if cs_scores else 0.0
    cs_col = df["country_uid"].map(cs_scores).fillna(cs_median)
    
    # 4. Blend conceded score (70%) and clean-sheet score (30%)
    df["defensive_record"] = 0.70 * inv_raw_01 + 0.30 * cs_col
    
    # 5. Invert so higher = worse, for zscore_cdf normalization
    df["defense_blended_raw"] = 1.0 - df["defensive_record"]
    
    # 6. Apply Z-score CDF and scale to [0, 1]
    df["A_defense_norm"] = normalize_zscore_cdf(df["defense_blended_raw"]) / 100.0

    # Component B
    df["B_attack_norm"] = _minmax(df["squad_attack_B"])
    df["B_defense_norm"] = _minmax(df["squad_defense_B"])

    # Component C: Elo
    df["C_norm"] = _minmax(df["elo_rating"])

    # Component D: recent form (already 0-1 scale but may need stretching)
    df["D_norm"] = _minmax(df["recent_form_D"])

    # ── Weighted combination ─────────────────────────────────────────────────
    aw = ATTACK_WEIGHTS
    dw = DEFENSE_WEIGHTS

    df["attack_rating_v2"] = (
        aw["recency"] * df["A_attack_norm"] +
        aw["squad"]   * df["B_attack_norm"] +
        aw["elo"]     * df["C_norm"]        +
        aw["form"]    * df["D_norm"]
    ) * 100.0

    df["defense_rating_v2"] = (
        dw["recency"] * df["A_defense_norm"] +
        dw["squad"]   * df["B_defense_norm"] +
        dw["elo"]     * df["C_norm"]         +
        dw["form"]    * df["D_norm"]
    ) * 100.0

    # Expose production names directly
    df["attack_rating"] = df["attack_rating_v2"]
    df["defense_rating"] = df["defense_rating_v2"]

    # ── Power Index & Rank (V2.1 Integration) ────────────────────────────────
    power_index_raw = (
        0.35 * (df["C_norm"] * 100.0) +
        0.20 * df["attack_rating"] +
        0.20 * df["defense_rating"] +
        0.15 * (df["squad_overall_strength"] * 100.0) +
        0.10 * (df["recent_form_D"] * 100.0)
    )
    df["power_index"] = _minmax(power_index_raw) * 100.0
    df["power_rank"] = df["power_index"].rank(ascending=False, method="min").astype(int)

    # Percentile rank for display only
    df["attack_v2_percentile"]  = _percentile_rank(df["attack_rating_v2"])
    df["defense_v2_percentile"] = _percentile_rank(df["defense_rating_v2"])

    # Component contributions (scaled to 0-100 for readability)
    df["comp_recency_attack"]  = df["A_attack_norm"]  * 100.0
    df["comp_squad_attack"]    = df["B_attack_norm"]  * 100.0
    df["comp_recency_defense"] = df["A_defense_norm"] * 100.0
    df["comp_squad_defense"]   = df["B_defense_norm"] * 100.0
    df["comp_elo"]             = df["C_norm"]         * 100.0
    df["comp_form"]            = df["D_norm"]         * 100.0

    return df


# ─────────────────────────────────────────────────────────────────────────────
# Validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_v2(df: pd.DataFrame) -> list[str]:
    """
    Run validation checks. Returns a list of warning strings.
    Hard errors (NaN/Inf/out-of-range) are raised as ValueError.
    Soft positional checks are warnings only.
    """
    warnings: list[str] = []

    # Hard checks
    for col in ["attack_rating_v2", "defense_rating_v2"]:
        bad_null = df[col].isna().sum()
        bad_inf  = df[col].apply(lambda x: math.isinf(x) if isinstance(x, float) else False).sum()
        bad_range = ((df[col] < 0) | (df[col] > 100)).sum()
        if bad_null:
            raise ValueError(f"{col}: {bad_null} null values found")
        if bad_inf:
            raise ValueError(f"{col}: {bad_inf} infinite values found")
        if bad_range:
            raise ValueError(f"{col}: {bad_range} values outside [0, 100]")

    # Soft positional checks — warn only, never abort
    atk_ranked = df.sort_values("attack_rating_v2", ascending=False).reset_index(drop=True)
    def_ranked  = df.sort_values("defense_rating_v2", ascending=False).reset_index(drop=True)

    watch_attack  = {"Spain": 10, "France": 10, "Argentina": 10, "Brazil": 15, "England": 15}
    watch_defense = {"Germany": 10, "Italy": 10, "France": 12, "Spain": 12, "Netherlands": 15}

    for country, threshold in watch_attack.items():
        row = atk_ranked[atk_ranked["country_name"] == country]
        if row.empty:
            continue
        rank = row.index[0] + 1
        if rank > threshold:
            warnings.append(f"WARN: {country} attack rank {rank} > expected top-{threshold}")

    for country, threshold in watch_defense.items():
        row = def_ranked[def_ranked["country_name"] == country]
        if row.empty:
            continue
        rank = row.index[0] + 1
        if rank > threshold:
            warnings.append(f"WARN: {country} defense rank {rank} > expected top-{threshold}")

    # Warn if a low-Elo team appears in top-5
    low_elo_threshold = 1600.0
    for _, r in atk_ranked.head(5).iterrows():
        if r["elo_rating"] < low_elo_threshold:
            warnings.append(
                f"WARN: {r['country_name']} in attack top-5 but Elo={r['elo_rating']:.0f} < {low_elo_threshold}"
            )
    for _, r in def_ranked.head(5).iterrows():
        if r["elo_rating"] < low_elo_threshold:
            warnings.append(
                f"WARN: {r['country_name']} in defense top-5 but Elo={r['elo_rating']:.0f} < {low_elo_threshold}"
            )

    return warnings


# ─────────────────────────────────────────────────────────────────────────────
# Diagnostic outputs
# ─────────────────────────────────────────────────────────────────────────────

def build_component_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """Distribution stats for each component score (0-100 scale)."""
    components = {
        "recency_attack":  "comp_recency_attack",
        "squad_attack":    "comp_squad_attack",
        "recency_defense": "comp_recency_defense",
        "squad_defense":   "comp_squad_defense",
        "elo":             "comp_elo",
        "form":            "comp_form",
        "attack_v2_final": "attack_rating_v2",
        "defense_v2_final":"defense_rating_v2",
    }
    rows = []
    for label, col in components.items():
        s = df[col]
        rows.append({
            "component": label,
            "min":    round(s.min(), 3),
            "p10":    round(s.quantile(0.10), 3),
            "p25":    round(s.quantile(0.25), 3),
            "median": round(s.median(), 3),
            "p75":    round(s.quantile(0.75), 3),
            "p90":    round(s.quantile(0.90), 3),
            "max":    round(s.max(), 3),
            "std":    round(s.std(), 3),
        })
    return pd.DataFrame(rows)


def build_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Correlation matrix between v1/v2 ratings, Elo, and form."""
    cols = {
        "attack_v1":      "attack_v1",
        "defense_v1":     "defense_v1",
        "attack_v2":      "attack_rating_v2",
        "defense_v2":     "defense_rating_v2",
        "elo":            "comp_elo",
        "form":           "comp_form",
        "recency_attack": "comp_recency_attack",
        "squad_attack":   "comp_squad_attack",
    }
    sub = df[[v for v in cols.values() if v in df.columns]].copy()
    sub.columns = [k for k, v in cols.items() if v in df.columns]
    return sub.corr().round(3)


def build_breakdown_json(df: pd.DataFrame, mode: str) -> dict:
    """
    Build per-team breakdown JSON.
    mode: 'attack' or 'defense'
    """
    out = {}
    for _, row in df.iterrows():
        team = str(row["country_name"])
        if mode == "attack":
            out[team] = {
                "team": team,
                "country_uid": row["country_uid"],
                "components": {
                    "recency_goals":  round(row["comp_recency_attack"], 2),
                    "squad_quality":  round(row["comp_squad_attack"],   2),
                    "elo":            round(row["comp_elo"],             2),
                    "recent_form":    round(row["comp_form"],            2),
                },
                "final_rating": round(row["attack_rating_v2"], 2),
                "v1_rating":    round(row["attack_v1"],         2),
                "delta":        round(row["attack_rating_v2"] - row["attack_v1"], 2),
            }
        else:
            out[team] = {
                "team": team,
                "country_uid": row["country_uid"],
                "components": {
                    "recency_conceded": round(row["comp_recency_defense"], 2),
                    "squad_quality":    round(row["comp_squad_defense"],   2),
                    "elo":              round(row["comp_elo"],              2),
                    "recent_form":      round(row["comp_form"],             2),
                },
                "final_rating": round(row["defense_rating_v2"], 2),
                "v1_rating":    round(row["defense_v1"],         2),
                "delta":        round(row["defense_rating_v2"] - row["defense_v1"], 2),
            }
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────────────────────────────────────

def export_all(df: pd.DataFrame) -> None:
    """Write all output files to processed/."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Comparison CSV
    comparison_cols = [
        "country_uid", "country_name", "elo_rating",
        "attack_v1", "attack_rating_v2", "attack_v2_percentile",
        "defense_v1", "defense_rating_v2", "defense_v2_percentile",
    ]
    comparison = df[comparison_cols].sort_values("attack_rating_v2", ascending=False)
    comparison.to_csv(PROCESSED_DIR / "attack_defense_ratings_v2_comparison.csv", index=False)
    logger.info("Wrote attack_defense_ratings_v2_comparison.csv")

    # Full components CSV
    df.to_csv(PROCESSED_DIR / "attack_defense_v2_components.csv", index=False)
    logger.info("Wrote attack_defense_v2_components.csv")

    # Component distribution
    dist = build_component_distribution(df)
    dist.to_csv(PROCESSED_DIR / "component_distribution.csv", index=False)
    logger.info("Wrote component_distribution.csv")

    # Correlation matrix
    corr = build_correlation_matrix(df)
    corr.to_csv(PROCESSED_DIR / "correlation_matrix.csv")
    logger.info("Wrote correlation_matrix.csv")

    # JSON breakdowns
    atk_json = build_breakdown_json(df, "attack")
    def_json  = build_breakdown_json(df, "defense")
    with open(PROCESSED_DIR / "attack_breakdown.json", "w", encoding="utf-8") as f:
        json.dump(atk_json, f, indent=2, ensure_ascii=False)
    with open(PROCESSED_DIR / "defense_breakdown.json", "w", encoding="utf-8") as f:
        json.dump(def_json, f, indent=2, ensure_ascii=False)
    logger.info("Wrote attack_breakdown.json and defense_breakdown.json")

    # Power rankings CSV
    power_cols = [
        "country_uid", "country_name", "power_rank", "power_index",
        "elo_rating", "attack_rating", "defense_rating",
        "squad_overall_strength", "recent_form_score"
    ]
    power_df = df.copy()
    power_df["recent_form_score"] = power_df["recent_form_D"]
    power_df = power_df[power_cols].sort_values("power_rank")
    power_df.to_csv(PROCESSED_DIR / "power_rankings.csv", index=False)
    logger.info("Wrote power_rankings.csv")
