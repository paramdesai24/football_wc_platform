"""
Entity Registry: Canonicalize football entities and resolve naming inconsistencies.

Handles:
- Country name mapping and normalization
- Club name normalization
- Competition name standardization
- Canonical entity lookups
- Fuzzy matching support (via rapidfuzz)
"""

import pandas as pd
from typing import Dict, Optional, Tuple, Any
import logging
from unidecode import unidecode

logger = logging.getLogger(__name__)

try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False
    logger.warning("rapidfuzz not available - fuzzy matching disabled")

# ============================================================================
# CANONICAL COUNTRY MAPPINGS
# ============================================================================

COUNTRY_CANONICAL_MAPPING = {
    # Primary names
    "Argentina": "Argentina",
    "Brazil": "Brazil",
    "France": "France",
    "Germany": "Germany",
    "England": "England",
    "Spain": "Spain",
    "Italy": "Italy",
    "Netherlands": "Netherlands",
    "Belgium": "Belgium",
    "Portugal": "Portugal",
    "Denmark": "Denmark",
    "Sweden": "Sweden",
    "Norway": "Norway",
    "Poland": "Poland",
    "Ukraine": "Ukraine",
    "Russia": "Russia",
    "Mexico": "Mexico",
    "Canada": "Canada",
    "United States": "United States",
    "Uruguay": "Uruguay",
    "Chile": "Chile",
    "Colombia": "Colombia",
    "Peru": "Peru",
    "Ecuador": "Ecuador",
    "Paraguay": "Paraguay",
    "Bolivia": "Bolivia",
    "Venezuela": "Venezuela",
    "Japan": "Japan",
    "South Korea": "South Korea",
    "Australia": "Australia",
    "India": "India",
    "China": "China",
    "Saudi Arabia": "Saudi Arabia",
    "Qatar": "Qatar",
    "United Arab Emirates": "United Arab Emirates",
    "Iran": "Iran",
    "Egypt": "Egypt",
    "Nigeria": "Nigeria",
    "Cameroon": "Cameroon",
    "South Africa": "South Africa",
    
    # Abbreviations
    "ARG": "Argentina",
    "BRA": "Brazil",
    "FRA": "France",
    "GER": "Germany",
    "ENG": "England",
    "ESP": "Spain",
    "ITA": "Italy",
    "NED": "Netherlands",
    "BEL": "Belgium",
    "POR": "Portugal",
    "DEN": "Denmark",
    "SWE": "Sweden",
    "NOR": "Norway",
    "POL": "Poland",
    "UKR": "Ukraine",
    "RUS": "Russia",
    "MEX": "Mexico",
    "CAN": "Canada",
    "USA": "United States",
    "URY": "Uruguay",
    "CHI": "Chile",
    "COL": "Colombia",
    "PER": "Peru",
    "ECU": "Ecuador",
    "PAR": "Paraguay",
    "BOL": "Bolivia",
    "VEN": "Venezuela",
    "JPN": "Japan",
    "KOR": "South Korea",
    "AUS": "Australia",
    "IND": "India",
    "CHN": "China",
    "SAU": "Saudi Arabia",
    "QAT": "Qatar",
    "UAE": "United Arab Emirates",
    "IRN": "Iran",
    "EGY": "Egypt",
    "NGA": "Nigeria",
    "CMR": "Cameroon",
    "RSA": "South Africa",
    
    # Variants
    "Argentina NT": "Argentina",
    "Argentina National Team": "Argentina",
    "Brazil NT": "Brazil",
    "Brazil National Team": "Brazil",
    "United States of America": "United States",
    "USA National Team": "United States",
    "South Korea NT": "South Korea",
    "Republic of Korea": "South Korea",
    "North Korea": "North Korea",
    "Czech Republic": "Czechia",
    "Republic of Czechia": "Czechia",
    "Czechia": "Czechia",
    "Wales": "Wales",
    "Scotland": "Scotland",
    "Northern Ireland": "Northern Ireland",
    "Republic of Ireland": "Ireland",
    "Ivory Coast": "Côte d'Ivoire",
    "Côte d'Ivoire": "Côte d'Ivoire",
    "Cote d'Ivoire": "Côte d'Ivoire",
    "Cape Verde": "Cape Verde",
    "New Zealand": "New Zealand",
    "Costa Rica": "Costa Rica",
    "Panama": "Panama",
    "Honduras": "Honduras",
    "Jamaica": "Jamaica",
    "Trinidad and Tobago": "Trinidad and Tobago",
    "New Caledonia": "New Caledonia",
    "Fiji": "Fiji",
    "Samoa": "Samoa",
}

# ISO 3166-1 alpha-2 codes
COUNTRY_ISO2_MAPPING = {
    "Argentina": "AR",
    "Brazil": "BR",
    "France": "FR",
    "Germany": "DE",
    "England": "GB-ENG",
    "Spain": "ES",
    "Italy": "IT",
    "Netherlands": "NL",
    "Belgium": "BE",
    "Portugal": "PT",
    "Denmark": "DK",
    "Sweden": "SE",
    "Norway": "NO",
    "Poland": "PL",
    "Ukraine": "UA",
    "Russia": "RU",
    "Mexico": "MX",
    "Canada": "CA",
    "United States": "US",
    "Uruguay": "UY",
    "Chile": "CL",
    "Colombia": "CO",
    "Peru": "PE",
    "Ecuador": "EC",
    "Paraguay": "PY",
    "Bolivia": "BO",
    "Venezuela": "VE",
    "Japan": "JP",
    "South Korea": "KR",
    "Australia": "AU",
    "India": "IN",
    "China": "CN",
    "Saudi Arabia": "SA",
    "Qatar": "QA",
    "United Arab Emirates": "AE",
    "Iran": "IR",
    "Egypt": "EG",
    "Nigeria": "NG",
    "Cameroon": "CM",
    "South Africa": "ZA",
    "Czechia": "CZ",
    "Wales": "GB-WLS",
    "Scotland": "GB-SCT",
    "Northern Ireland": "GB-NIR",
    "Ireland": "IE",
    "Côte d'Ivoire": "CI",
}

# ============================================================================
# CANONICAL CLUB MAPPINGS
# ============================================================================

CLUB_CANONICAL_MAPPING = {
    "Manchester United": "Manchester United",
    "Man Utd": "Manchester United",
    "Man United": "Manchester United",
    "Manchester City": "Manchester City",
    "Man City": "Manchester City",
    "Liverpool": "Liverpool",
    "Arsenal": "Arsenal",
    "Chelsea": "Chelsea",
    "Tottenham": "Tottenham Hotspur",
    "Tottenham Hotspur": "Tottenham Hotspur",
    "Real Madrid": "Real Madrid",
    "FC Barcelona": "FC Barcelona",
    "Barcelona": "FC Barcelona",
    "Barca": "FC Barcelona",
    "FC Bayern Munich": "FC Bayern Munich",
    "Bayern Munich": "FC Bayern Munich",
    "Bayern": "FC Bayern Munich",
    "Borussia Dortmund": "Borussia Dortmund",
    "BVB": "Borussia Dortmund",
    "AC Milan": "AC Milan",
    "Milan": "AC Milan",
    "Inter Milan": "Inter Milan",
    "Internazionale": "Inter Milan",
    "Juventus": "Juventus",
    "Roma": "AS Roma",
    "AS Roma": "AS Roma",
    "PSG": "Paris Saint-Germain",
    "Paris Saint-Germain": "Paris Saint-Germain",
    "Paris SG": "Paris Saint-Germain",
}

# ============================================================================
# COMPETITION MAPPINGS
# ============================================================================

COMPETITION_CANONICAL_MAPPING = {
    "Premier League": "Premier League",
    "La Liga": "La Liga",
    "Serie A": "Serie A",
    "Bundesliga": "Bundesliga",
    "Ligue 1": "Ligue 1",
    "Eredivisie": "Eredivisie",
    "Champions League": "UEFA Champions League",
    "UEFA Champions League": "UEFA Champions League",
    "CL": "UEFA Champions League",
    "Europa League": "UEFA Europa League",
    "UEFA Europa League": "UEFA Europa League",
    "EL": "UEFA Europa League",
    "World Cup": "FIFA World Cup",
    "FIFA World Cup": "FIFA World Cup",
    "Euro": "UEFA European Championship",
    "UEFA European Championship": "UEFA European Championship",
    "Copa America": "Copa América",
    "Copa América": "Copa América",
    "African Cup of Nations": "Africa Cup of Nations",
    "AFCON": "Africa Cup of Nations",
    "Asia Cup": "AFC Asian Cup",
    "AFC Asian Cup": "AFC Asian Cup",
    "Confederation Cup": "FIFA Confederations Cup",
    "Olympics": "Summer Olympics",
}

# ============================================================================
# CONFEDERATION MAPPINGS
# ============================================================================

CONFEDERATION_MAPPING = {
    "CONMEBOL": "CONMEBOL",
    "UEFA": "UEFA",
    "CAF": "CAF",
    "AFC": "AFC",
    "CONCACAF": "CONCACAF",
    "OFC": "OFC",
}

# ============================================================================
# POSITION MAPPINGS (normalize to standardized positions)
# ============================================================================

POSITION_CANONICAL_MAPPING = {
    "Goalkeeper": "GK",
    "GK": "GK",
    "Defender": "DEF",
    "DEF": "DEF",
    "CB": "DEF",
    "RB": "DEF",
    "LB": "DEF",
    "LWB": "DEF",
    "RWB": "DEF",
    "Midfielder": "MID",
    "MID": "MID",
    "CM": "MID",
    "CDM": "MID",
    "CAM": "MID",
    "RM": "MID",
    "LM": "MID",
    "Forward": "FWD",
    "FWD": "FWD",
    "ST": "FWD",
    "CF": "FWD",
    "RW": "FWD",
    "LW": "FWD",
    "RF": "FWD",
    "LF": "FWD",
    "Winger": "FWD",
}


class EntityRegistry:
    """
    Centralized entity canonicalization and lookup system.
    """

    def __init__(self):
        self.fuzzy_cache = {}
        self.FUZZY_THRESHOLD = 85  # Min score for fuzzy matching

    def canonicalize_country(self, country_name: Optional[str]) -> Optional[str]:
        """
        Convert country name/code to canonical form.

        Args:
            country_name: Input country name or code

        Returns:
            Canonical country name or None
        """
        if not country_name or pd.isna(country_name):
            return None

        country_name = str(country_name).strip()

        # Direct lookup
        if country_name in COUNTRY_CANONICAL_MAPPING:
            return COUNTRY_CANONICAL_MAPPING[country_name]

        # Case-insensitive lookup
        for key, canonical in COUNTRY_CANONICAL_MAPPING.items():
            if key.lower() == country_name.lower():
                return canonical

        # Fuzzy matching if rapidfuzz available
        if RAPIDFUZZ_AVAILABLE:
            match = self._fuzzy_lookup(country_name, COUNTRY_CANONICAL_MAPPING)
            if match:
                return match

        logger.debug(f"Could not canonicalize country: {country_name}")
        return None

    def get_country_iso2(self, country_name: str) -> Optional[str]:
        """Get ISO 3166-1 alpha-2 code for country."""
        canonical = self.canonicalize_country(country_name)
        if canonical:
            return COUNTRY_ISO2_MAPPING.get(canonical)
        return None

    def canonicalize_club(self, club_name: Optional[str]) -> Optional[str]:
        """Convert club name to canonical form."""
        if not club_name or pd.isna(club_name):
            return None

        club_name = str(club_name).strip()

        if club_name in CLUB_CANONICAL_MAPPING:
            return CLUB_CANONICAL_MAPPING[club_name]

        for key, canonical in CLUB_CANONICAL_MAPPING.items():
            if key.lower() == club_name.lower():
                return canonical

        if RAPIDFUZZ_AVAILABLE:
            match = self._fuzzy_lookup(club_name, CLUB_CANONICAL_MAPPING)
            if match:
                return match

        return None

    def canonicalize_competition(self, competition_name: Optional[str]) -> Optional[str]:
        """Convert competition name to canonical form."""
        if not competition_name or pd.isna(competition_name):
            return None

        competition_name = str(competition_name).strip()

        if competition_name in COMPETITION_CANONICAL_MAPPING:
            return COMPETITION_CANONICAL_MAPPING[competition_name]

        for key, canonical in COMPETITION_CANONICAL_MAPPING.items():
            if key.lower() == competition_name.lower():
                return canonical

        if RAPIDFUZZ_AVAILABLE:
            match = self._fuzzy_lookup(competition_name, COMPETITION_CANONICAL_MAPPING)
            if match:
                return match

        return None

    def canonicalize_position(self, position: Optional[str]) -> Optional[str]:
        """Normalize position to standard form."""
        if not position or pd.isna(position):
            return None

        position = str(position).strip()

        if position in POSITION_CANONICAL_MAPPING:
            return POSITION_CANONICAL_MAPPING[position]

        for key, canonical in POSITION_CANONICAL_MAPPING.items():
            if key.lower() == position.lower():
                return canonical

        return None

    def _fuzzy_lookup(self, query: str, mapping: Dict[str, str]) -> Optional[str]:
        """
        Fuzzy match query against mapping keys.

        Args:
            query: Input string
            mapping: Mapping to search

        Returns:
            Mapped value if match score >= threshold, else None
        """
        if query in self.fuzzy_cache:
            return self.fuzzy_cache[query]

        best_match = None
        best_score = 0

        for key in mapping:
            score = fuzz.token_set_ratio(query.lower(), key.lower())
            if score > best_score:
                best_score = score
                best_match = mapping[key]

        if best_score >= self.FUZZY_THRESHOLD:
            self.fuzzy_cache[query] = best_match
            return best_match

        self.fuzzy_cache[query] = None
        return None

    def remove_accents(self, text: Optional[str]) -> Optional[str]:
        """Remove accents from text (e.g., Mbappé → Mbappe)."""
        if not text or pd.isna(text):
            return None
        return unidecode(text)

    def normalize_string(self, text: Optional[str]) -> Optional[str]:
        """
        Normalize string: lowercase, remove accents, strip whitespace.
        """
        if not text or pd.isna(text):
            return None
        return self.remove_accents(text).lower().strip()


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_entity_registry = EntityRegistry()


def canonicalize_country(country_name: Optional[str]) -> Optional[str]:
    """Canonicalize country name."""
    return _entity_registry.canonicalize_country(country_name)


def canonicalize_club(club_name: Optional[str]) -> Optional[str]:
    """Canonicalize club name."""
    return _entity_registry.canonicalize_club(club_name)


def canonicalize_competition(competition_name: Optional[str]) -> Optional[str]:
    """Canonicalize competition name."""
    return _entity_registry.canonicalize_competition(competition_name)


def canonicalize_position(position: Optional[str]) -> Optional[str]:
    """Canonicalize position."""
    return _entity_registry.canonicalize_position(position)


def get_country_iso2(country_name: str) -> Optional[str]:
    """Get ISO 3166-1 alpha-2 code."""
    return _entity_registry.get_country_iso2(country_name)


def normalize_string(text: Optional[str]) -> Optional[str]:
    """Normalize string."""
    return _entity_registry.normalize_string(text)


def remove_accents(text: Optional[str]) -> Optional[str]:
    """Remove accents."""
    return _entity_registry.remove_accents(text)
