"""Aggregation package for squad and country level aggregations."""

from .squad_aggregator import SquadAggregator
from .country_aggregator import CountryAggregator

__all__ = ["SquadAggregator", "CountryAggregator"]
