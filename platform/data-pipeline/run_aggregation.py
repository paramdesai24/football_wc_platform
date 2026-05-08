"""Entrypoint: Run aggregation steps to produce squad and country aggregates."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

from aggregation.country_aggregator import CountryAggregator
from aggregation.squad_aggregator import SquadAggregator
from feature_engineering.country_features import CountryFeatureEngineering
from ingestion.loader import DataLoader, save_csv
from utils.config import get_processed_paths
from utils.constants import DATASETS
from utils.entity_registry import canonicalize_club, canonicalize_country, get_country_iso2
from utils.logging_utils import setup_logger
from utils.quality_systems import (
    ConfidenceScorer,
    DataQualityTier,
    FeatureLineageTracker,
    ReliabilityWeighting,
)

logger = setup_logger("pipeline", "pipeline.log")


def _stable_uid(prefix: str, value: str) -> str:
    normalized = " ".join(str(value).strip().lower().split())
    digest = hashlib.sha1(normalized.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}_{digest}"


def _build_player_ids(players: pd.DataFrame) -> pd.DataFrame:
    working = players.copy()
    working["country"] = working.get("country_of_citizenship", working.get("country", pd.Series(index=working.index))).apply(canonicalize_country)
    working["country_uid"] = working["country"].apply(lambda value: f"C_{get_country_iso2(value) or _stable_uid('C', value)[:6]}")
    
    # Generate stable club_uid for each player
    def _make_club_uid(row):
        # Try multiple club ID sources for explicit numeric ID
        for id_col in ["club_id", "current_club_id", "club_id_transfermarket"]:
            if id_col in row and pd.notna(row[id_col]):
                try:
                    cid = int(row[id_col])
                    if cid > 0:
                        return f"CL_{cid}"
                except (ValueError, TypeError):
                    pass
        
        # Try multiple club name sources
        club_name = None
        for name_col in ["current_club_name", "club", "club_name"]:
            if name_col in row and pd.notna(row[name_col]):
                club_name = str(row[name_col]).strip()
                if club_name:
                    break
        
        # Generate stable UID from club name or fallback
        if club_name:
            canonical_name = canonicalize_club(club_name)
            return _stable_uid("CL", canonical_name or club_name)
        return _stable_uid("CL", "unknown_club")
    
    working["club_uid"] = working.apply(_make_club_uid, axis=1)
    working["player_uid"] = working.apply(
        lambda row: f"P_{row['player_id']}_{row['country_uid'] if pd.notna(row['country_uid']) else _stable_uid('C', row.get('country', 'unknown'))}",
        axis=1,
    )
    return working


def _calculate_player_confidence(players: pd.DataFrame) -> pd.DataFrame:
    working = players.copy()

    for column in ["games_played", "minutes_played", "recent_match_count", "days_since_last_match"]:
        if column not in working.columns:
            working[column] = 0

    working["games_played"] = pd.to_numeric(working["games_played"], errors="coerce").fillna(0)
    working["minutes_played"] = pd.to_numeric(working["minutes_played"], errors="coerce").fillna(0)
    working["recent_match_count"] = pd.to_numeric(working["recent_match_count"], errors="coerce").fillna(0)
    working["days_since_last_match"] = pd.to_numeric(working["days_since_last_match"], errors="coerce").fillna(9999)

    working["confidence_score"] = working.apply(
        lambda row: ConfidenceScorer.calculate_player_confidence(
            appearances=int(row.get("games_played", 0) or 0),
            minutes_played=float(row.get("minutes_played", 0) or 0),
            recent_match_count=int(row.get("recent_match_count", 0) or 0),
            days_since_last_match=int(row.get("days_since_last_match", 9999) or 9999),
            field_completeness=min(row.count() / max(len(row), 1), 1.0),
        ),
        axis=1,
    )
    return working


def _apply_country_quality(country_metrics: pd.DataFrame) -> pd.DataFrame:
    working = country_metrics.copy()

    if "country" in working.columns:
        working["country"] = working["country"].apply(canonicalize_country)
        working["country_uid"] = working["country"].apply(lambda value: f"C_{get_country_iso2(value) or _stable_uid('C', value)[:6]}")

    if "recent_matches" not in working.columns:
        working["recent_matches"] = 0
    if "total_matches" not in working.columns:
        working["total_matches"] = 0

    working["recent_matches"] = pd.to_numeric(working["recent_matches"], errors="coerce").fillna(0)
    working["total_matches"] = pd.to_numeric(working["total_matches"], errors="coerce").fillna(0)

    working["confidence_score"] = working.apply(
        lambda row: min(
            1.0,
            0.45 * min(float(row.get("total_matches", 0) or 0) / 50.0, 1.0)
            + 0.25 * min(float(row.get("recent_matches", 0) or 0) / 10.0, 1.0)
            + 0.30 * min(row.count() / max(len(row), 1), 1.0),
        ),
        axis=1,
    )
    return working


def main():
    logger.info("Starting aggregation run...")
    loader = DataLoader(DATASETS)
    loader.load_all()

    processed_paths = get_processed_paths()
    out_dir = processed_paths["pipeline_processed"]

    def load_csv_if_exists(filename: str) -> pd.DataFrame:
        path = out_dir / filename
        return pd.read_csv(path) if path.exists() else pd.DataFrame()

    cleaned_players = load_csv_if_exists("cleaned_players.csv")
    cleaned_valuations = load_csv_if_exists("cleaned_valuations.csv")
    player_per90 = load_csv_if_exists("player_per90.csv")
    player_form_scores = load_csv_if_exists("player_form_scores.csv")
    player_consistency_scores = load_csv_if_exists("player_consistency_scores.csv")
    country_stats = load_csv_if_exists("country_stats.csv")
    country_recent_form = load_csv_if_exists("country_recent_form.csv")
    cleaned_results = load_csv_if_exists("cleaned_results.csv")
    cleaned_appearances = load_csv_if_exists("cleaned_appearances.csv")

    master_players = cleaned_players.copy()
    if not master_players.empty:
        if "country_of_citizenship" not in master_players.columns and "country" in master_players.columns:
            master_players["country_of_citizenship"] = master_players["country"]
        if not cleaned_valuations.empty and "player_id" in cleaned_valuations.columns:
            valuations_latest = cleaned_valuations.sort_values(by=[col for col in ["date"] if col in cleaned_valuations.columns], ascending=False)
            if "player_id" in valuations_latest.columns:
                valuations_latest = valuations_latest.drop_duplicates(subset=["player_id"], keep="first")
            if "market_value_in_eur" in valuations_latest.columns:
                valuations_latest = valuations_latest[["player_id", "market_value_in_eur"]].rename(columns={"market_value_in_eur": "market_value"})
                master_players = master_players.merge(valuations_latest, on="player_id", how="left")
        if not player_per90.empty and "player_id" in player_per90.columns:
            master_players = master_players.merge(player_per90, on="player_id", how="left")
        if not player_form_scores.empty and "player_id" in player_form_scores.columns:
            master_players = master_players.merge(player_form_scores, on="player_id", how="left")
        if not player_consistency_scores.empty and "player_id" in player_consistency_scores.columns:
            master_players = master_players.merge(player_consistency_scores, on="player_id", how="left")

        if not cleaned_appearances.empty and "player_id" in cleaned_appearances.columns:
            appearance_summary = cleaned_appearances[[col for col in ["player_id", "date", "minutes_played"] if col in cleaned_appearances.columns]].copy()
            if "date" in appearance_summary.columns:
                appearance_summary["date"] = pd.to_datetime(appearance_summary["date"], errors="coerce")
                recent_cutoff = pd.Timestamp.now() - pd.Timedelta(days=365)
                recent_counts = (
                    appearance_summary[appearance_summary["date"] >= recent_cutoff]
                    .groupby("player_id")
                    .size()
                    .rename("recent_match_count")
                )
                last_match = appearance_summary.groupby("player_id")["date"].max().rename("last_match_date")
                appearance_summary = pd.concat([recent_counts, last_match], axis=1).reset_index()
                appearance_summary["days_since_last_match"] = (
                    pd.Timestamp.now() - pd.to_datetime(appearance_summary["last_match_date"], errors="coerce")
                ).dt.days.fillna(9999)
                appearance_summary = appearance_summary[["player_id", "recent_match_count", "days_since_last_match"]]
                master_players = master_players.merge(appearance_summary, on="player_id", how="left")

        master_players = _build_player_ids(master_players)
        master_players = _calculate_player_confidence(master_players)
        master_players = DataQualityTier.add_data_quality_tier(master_players)
        master_players["impact_score"] = master_players[["contribution_per_90", "form_score"]].fillna(0).prod(axis=1)
        master_players = ReliabilityWeighting.apply_reliability_weighting(
            master_players,
            ["form_score", "impact_score"],
        )

    if not country_stats.empty and not country_recent_form.empty and "country" in country_stats.columns and "country" in country_recent_form.columns:
        recent_form_map = {
            row["country"]: (
                float(row.get("recent_form_score", 0.5)),
                int(row.get("recent_matches", 0) or 0),
            )
            for _, row in country_recent_form.iterrows()
        }
        country_metrics = CountryFeatureEngineering.create_master_countries(country_stats, recent_form_map)
    else:
        country_metrics = CountryAggregator.create_country_metrics(cleaned_results) if not cleaned_results.empty else pd.DataFrame()

    if not country_metrics.empty:
        country_metrics = _apply_country_quality(country_metrics)
        country_metrics["attack_rating_value"] = country_metrics.get("attack_rating", 0)
        country_metrics["attack_rating_confidence"] = country_metrics["confidence_score"]
        country_metrics["defense_rating_value"] = country_metrics.get("defense_rating", 0)
        country_metrics["defense_rating_confidence"] = country_metrics["confidence_score"]
        if "historical_strength" in country_metrics.columns:
            country_metrics["impact_score"] = country_metrics["historical_strength"]
        else:
            country_metrics["impact_score"] = country_metrics.get("win_rate", 0) * 100
        country_metrics = ReliabilityWeighting.apply_reliability_weighting(
            country_metrics,
            ["attack_rating", "defense_rating", "impact_score"],
        )

    squads = SquadAggregator.aggregate(master_players) if not master_players.empty else pd.DataFrame()
    if not squads.empty:
        squads["country"] = squads["country"].apply(canonicalize_country)
        squads["country_uid"] = squads["country"].apply(lambda value: f"C_{get_country_iso2(value) or _stable_uid('C', value)[:6]}")
        squads["confidence_score"] = squads.apply(
            lambda row: min(1.0, 0.5 * min(float(row.get("squad_size", 0) or 0) / 23.0, 1.0) + 0.5 * min(row.count() / max(len(row), 1), 1.0)),
            axis=1,
        )
        squads = DataQualityTier.add_data_quality_tier(squads)

    lineage = FeatureLineageTracker()
    if not master_players.empty:
        lineage.record_source("player_uid", "cleaned_players", ["player_id", "country_of_citizenship", "club"])
        lineage.record_source("confidence_score", "cleaned_players+cleaned_appearances", ["games_played", "minutes_played", "recent_match_count", "days_since_last_match"])
        lineage.record_transformation("confidence_score", "confidence_scoring", {"system": "ConfidenceScorer"})
        lineage.record_transformation("data_quality_tier", "tiering", {"system": "DataQualityTier"})
        lineage.record_transformation("form_score", "reliability_weighting", {"system": "ReliabilityWeighting"})
    if not country_metrics.empty:
        lineage.record_source("country_uid", "country_stats+country_recent_form", ["country", "recent_form_score", "recent_matches"])
        lineage.record_transformation("attack_rating", "country_estimation", {"system": "CountryFeatureEngineering"})
    lineage.export_lineage(out_dir / "feature_lineage.json")

    player_form = pd.DataFrame()
    if not master_players.empty:
        player_form_columns = [
            "player_id",
            "player_uid",
            "country_uid",
            "club_uid",
            "form_score",
            "form_score_value",
            "form_score_confidence",
            "confidence_score",
            "data_quality_tier",
            "consistency_score",
            "contribution_per_90",
            "impact_score",
            "impact_score_confidence",
        ]
        existing_columns = [column for column in player_form_columns if column in master_players.columns]
        player_form = master_players[existing_columns].copy()

    if not master_players.empty:
        save_csv(master_players, out_dir / "master_players.csv")
    if not player_form.empty:
        save_csv(player_form, out_dir / "player_form.csv")
    if not country_metrics.empty:
        save_csv(country_metrics, out_dir / "master_countries.csv")
        save_csv(country_metrics, out_dir / "country_strength.csv")

    if squads is not None:
        save_csv(squads, out_dir / "squad_aggregates.csv")
    if country_metrics is not None and not country_metrics.empty:
        save_csv(country_metrics, out_dir / "country_aggregates.csv")

    if not squads.empty:
        save_csv(squads, out_dir / "squad_aggregates.csv")

    logger.info("Aggregation run completed")


if __name__ == "__main__":
    main()
