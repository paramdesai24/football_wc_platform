from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


def sanitize_jsonable(data: Any) -> Any:
    if isinstance(data, dict):
        return {key: sanitize_jsonable(value) for key, value in data.items()}
    if isinstance(data, list):
        return [sanitize_jsonable(item) for item in data]
    if isinstance(data, tuple):
        return [sanitize_jsonable(item) for item in data]
    if hasattr(data, "item") and callable(getattr(data, "item")):
        try:
            return data.item()
        except Exception:
            pass
    if isinstance(data, (str, int, float, bool)) or data is None:
        return data
    return str(data)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError:
        return default


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(sanitize_jsonable(data), handle, indent=2, ensure_ascii=False)


def ensure_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}