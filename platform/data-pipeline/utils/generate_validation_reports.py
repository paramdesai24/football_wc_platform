"""Generate validation reports for architecture, entities, confidence and quality.

Writes JSON files into the pipeline logs directory.
"""
import json
from pathlib import Path
import pandas as pd
from utils.constants import PROCESSED_DATA_DIR, LOGS_DIR


def load_csv(name: str) -> pd.DataFrame:
    path = PROCESSED_DATA_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def main():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    master_players = load_csv("master_players.csv")
    master_countries = load_csv("master_countries.csv")

    # Architecture validation
    arch = {
        "master_players_exists": not master_players.empty,
        "master_countries_exists": not master_countries.empty,
        "players_count": int(len(master_players)) if not master_players.empty else 0,
        "countries_count": int(len(master_countries)) if not master_countries.empty else 0,
    }

    # Entity validation
    entity = {}
    if not master_players.empty:
        uid_col = "player_uid" if "player_uid" in master_players.columns else "player_id"
        unique_uids = master_players[uid_col].nunique(dropna=True)
        total = len(master_players)
        entity["uid_column"] = uid_col
        entity["unique_uids"] = int(unique_uids)
        entity["total_records"] = int(total)
        entity["uid_unique_ratio"] = float(unique_uids) / max(1, total)
    else:
        entity = {"note": "no master_players available"}

    # Confidence validation
    confidence = {}
    if not master_players.empty and "confidence_score" in master_players.columns:
        conf = master_players["confidence_score"].dropna()
        confidence["min"] = float(conf.min()) if not conf.empty else None
        confidence["max"] = float(conf.max()) if not conf.empty else None
        confidence["mean"] = float(conf.mean()) if not conf.empty else None
        # distribution
        confidence["distribution_by_tier"] = (
            master_players.groupby("data_quality_tier").size().to_dict()
            if "data_quality_tier" in master_players.columns
            else {}
        )
    else:
        confidence = {"note": "confidence_score not present"}

    # Quality validation
    quality = {}
    if not master_players.empty and "data_quality_tier" in master_players.columns:
        quality["tier_counts"] = master_players["data_quality_tier"].fillna("UNKNOWN").value_counts().to_dict()
    else:
        quality = {"note": "data_quality_tier not present"}

    # Write reports
    (LOGS_DIR / "architecture_validation.json").write_text(json.dumps(arch, indent=2))
    (LOGS_DIR / "entity_validation_report.json").write_text(json.dumps(entity, indent=2))
    (LOGS_DIR / "confidence_validation_report.json").write_text(json.dumps(confidence, indent=2))
    (LOGS_DIR / "quality_validation_report.json").write_text(json.dumps(quality, indent=2))


if __name__ == "__main__":
    main()
