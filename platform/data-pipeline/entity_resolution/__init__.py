"""
Entity Resolution Module: Merge duplicate entities and resolve naming inconsistencies.

Sub-modules:
- player_resolution: Deduplicate players, merge records
- country_resolution: Canonicalize countries, merge stats
- club_resolution: Deduplicate clubs, resolve aliases
- competition_resolution: Standardize competitions

This module treats the system as a football knowledge graph where
players, countries, clubs, and competitions are interconnected entities.
"""

from .player_resolution import PlayerResolver
from .country_resolution import CountryResolver
from .club_resolution import ClubResolver
from .competition_resolution import CompetitionResolver

__all__ = [
    "PlayerResolver",
    "CountryResolver",
    "ClubResolver",
    "CompetitionResolver",
]
