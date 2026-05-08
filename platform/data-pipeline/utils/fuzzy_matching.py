"""
Lightweight fuzzy matching utilities for football entity resolution.

Supports:
- Accent removal
- Abbreviation normalization
- Whitespace and casing normalization
- Cached fuzzy lookups to avoid repeated computation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Tuple

import pandas as pd

from unidecode import unidecode

try:
    from rapidfuzz import process, fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:  # pragma: no cover
    process = None
    fuzz = None
    RAPIDFUZZ_AVAILABLE = False


ABBREVIATION_MAP = {
    "man utd": "manchester united",
    "man united": "manchester united",
    "man city": "manchester city",
    "psg": "paris saint-germain",
    "bvb": "borussia dortmund",
    "barca": "fc barcelona",
    "cfc": "chelsea",
    "utd": "united",
    "a.c. milan": "ac milan",
    "inter milan": "inter milan",
}


def normalize_text(value: Optional[str]) -> Optional[str]:
    """Normalize text for matching."""
    if value is None or pd.isna(value):
        return None

    normalized = unidecode(str(value)).strip().lower()
    normalized = " ".join(normalized.split())
    return ABBREVIATION_MAP.get(normalized, normalized)


@dataclass
class FuzzyMatchCache:
    """Cache fuzzy match results to avoid repeated work."""

    threshold: int = 85
    cache: Dict[str, Optional[str]] = field(default_factory=dict)

    def match(self, query: Optional[str], choices: Iterable[str]) -> Optional[str]:
        """Return the best match or None."""
        normalized_query = normalize_text(query)
        if not normalized_query:
            return None

        if normalized_query in self.cache:
            return self.cache[normalized_query]

        choice_map = {normalize_text(choice): choice for choice in choices if normalize_text(choice)}
        normalized_choices = list(choice_map.keys())

        if not normalized_choices:
            self.cache[normalized_query] = None
            return None

        if RAPIDFUZZ_AVAILABLE:
            best = process.extractOne(
                normalized_query,
                normalized_choices,
                scorer=fuzz.token_set_ratio,
            )
            if best and best[1] >= self.threshold:
                resolved = choice_map[best[0]]
                self.cache[normalized_query] = resolved
                return resolved

        # Lightweight fallback if rapidfuzz is unavailable.
        for candidate in normalized_choices:
            if normalized_query == candidate:
                resolved = choice_map[candidate]
                self.cache[normalized_query] = resolved
                return resolved

        self.cache[normalized_query] = None
        return None


_GLOBAL_CACHE = FuzzyMatchCache()


def fuzzy_match(query: Optional[str], choices: Iterable[str], threshold: int = 85) -> Optional[str]:
    """Convenience wrapper around the shared fuzzy matcher."""
    _GLOBAL_CACHE.threshold = threshold
    return _GLOBAL_CACHE.match(query, choices)
