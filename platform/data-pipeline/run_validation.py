"""Validation runner for the pipeline.

Run with: python -m run_validation (from platform/data-pipeline)

Performs dataset checks, UID uniqueness, confidence ranges, entity normalization,
loads processed datasets from centralized location, and inspects the SQLite DB.
"""
import json
from pathlib import Path
import sqlite3
import logging

import pandas as pd

from utils import generate_validation_reports
from utils.constants import PROCESSED_DATA_DIR, LOGS_DIR
from utils.config import DATABASE_PATH, get_processed_paths

logger = logging.getLogger("run_validation")


def _load_df(name: str) -> pd.DataFrame:
    p = PROCESSED_DATA_DIR / name
    if not p.exists():
        logger.warning(f"Missing processed file: {p}")
        return pd.DataFrame()
    return pd.read_csv(p)


def _check_uid_uniqueness(df: pd.DataFrame, col: str) -> dict:
    if df.empty or col not in df.columns:
        return {"column": col, "present": False}
    total = len(df)
    dup = df.duplicated(subset=[col]).sum()
    unique = df[col].nunique(dropna=True)
    return {"column": col, "present": True, "total": int(total), "unique": int(unique), "duplicates": int(dup)}


def _check_confidence(df: pd.DataFrame, col: str = "confidence_score") -> dict:
    if df.empty or col not in df.columns:
        return {"column": col, "present": False}
    vals = df[col].dropna()
    out_of_range = ((vals < 0) | (vals > 1)).sum()
    return {"column": col, "present": True, "count": int(len(vals)), "out_of_range": int(out_of_range)}


def _inspect_db(db_path: Path) -> dict:
    res = {}
    if not db_path.exists():
        return {"db_exists": False}
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cur.fetchall()]
        res["db_exists"] = True
        res["tables"] = {}
        for t in tables:
            try:
                cur.execute(f"SELECT COUNT(1) FROM '{t}'")
                cnt = cur.fetchone()[0]
            except Exception:
                cnt = None
            res["tables"][t] = cnt
        conn.close()
    except Exception as e:
        res["error"] = str(e)
    return res


def main():
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    # Generate baseline JSON reports via the utils module (module-style import)
    try:
        generate_validation_reports.main()
    except Exception as e:
        logger.error(f"Validation report generation failed: {e}")

    # Load master files
    master_players = _load_df("master_players.csv")
    master_countries = _load_df("master_countries.csv")

    summary = {}
    # UID checks
    summary["player_uid"] = _check_uid_uniqueness(master_players, "player_uid")
    summary["country_uid"] = _check_uid_uniqueness(master_countries, "country_uid")
    summary["club_uid"] = _check_uid_uniqueness(master_players, "club_uid")

    # Confidence checks
    summary["player_confidence"] = _check_confidence(master_players, "confidence_score")
    summary["country_confidence"] = _check_confidence(master_countries, "confidence_score")

    # Entity normalization checks (country naming)
    cn_check = {"duplicates_after_normalization": 0, "distinct_normalized": 0}
    if not master_countries.empty and "country" in master_countries.columns:
        normalized = master_countries["country"].astype(str).str.strip().str.lower()
        cn_check["distinct_normalized"] = int(normalized.nunique())
        cn_check["original_count"] = int(len(master_countries))
        cn_check["duplicates_after_normalization"] = int(len(master_countries) - normalized.nunique())
    summary["country_normalization"] = cn_check

    # Load a small set of processed datasets to ensure they load
    required_files = ["player_form.csv", "country_strength.csv", "squad_aggregates.csv", "feature_lineage.json"]
    loads = {}
    for fname in required_files:
        p = PROCESSED_DATA_DIR / fname
        loads[fname] = p.exists()
    summary["processed_loads"] = loads

    # Inspect SQLite DB
    db_summary = _inspect_db(DATABASE_PATH)
    summary["database"] = db_summary

    # Write summary
    out = LOGS_DIR / "validation_summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print(f"Validation summary written to {out}")


if __name__ == "__main__":
    main()
