from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from .state_store import load_json, save_json


BACKEND_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
HISTORY_FILE = BACKEND_DATA_DIR / "prediction_history.json"
MAX_HISTORY = 5


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_history() -> List[Dict[str, Any]]:
    history = load_json(HISTORY_FILE, [])
    if not isinstance(history, list):
        return []
    return history


def append_prediction(entry: Dict[str, Any]) -> List[Dict[str, Any]]:
    history = load_history()
    record = dict(entry)
    record["timestamp"] = record.get("timestamp") or _utc_now()
    history.append(record)
    trimmed = history[-MAX_HISTORY:]
    save_json(HISTORY_FILE, trimmed)
    return list(reversed(trimmed))


def get_recent_predictions(limit: int = MAX_HISTORY) -> List[Dict[str, Any]]:
    history = load_history()
    if limit <= 0:
        return []
    return list(reversed(history[-limit:]))