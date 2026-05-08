"""
Validation and normalization utilities.
"""

import re
import unicodedata
from typing import Optional, Tuple, List
from utils.constants import COUNTRY_MAPPINGS


def normalize_string(s: Optional[str]) -> str:
    """Normalize a string: remove accents, lowercase, trim whitespace."""
    if s is None or (isinstance(s, float)):
        return ""
    s = str(s).strip()
    # Remove accents
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    return s.lower()


def normalize_player_name(name: Optional[str]) -> str:
    """Normalize player name."""
    if not name or (isinstance(name, float)):
        return ""
    name = str(name).strip()
    # Remove extra spaces
    name = re.sub(r"\s+", " ", name)
    return name


def normalize_country(country: Optional[str]) -> str:
    """Normalize country name using mapping table."""
    if not country or (isinstance(country, float)):
        return ""
    country = str(country).strip()
    # Try direct mapping
    if country in COUNTRY_MAPPINGS:
        return COUNTRY_MAPPINGS[country]
    # Try normalized version
    normalized = normalize_string(country)
    for key, value in COUNTRY_MAPPINGS.items():
        if normalize_string(key) == normalized:
            return value
    # Return original if no mapping found
    return country


def normalize_position(pos: Optional[str]) -> str:
    """Normalize position code."""
    if not pos or (isinstance(pos, float)):
        return "Unknown"
    pos = str(pos).strip().upper()
    # Handle multi-position format (e.g., "GK,CB" -> "GK")
    if "," in pos:
        pos = pos.split(",")[0].strip()
    return pos


def normalize_club_name(club: Optional[str]) -> str:
    """Normalize club name."""
    if not club or (isinstance(club, float)):
        return ""
    club = str(club).strip()
    # Remove common suffixes
    club = re.sub(r" (F\.C\.|FC|F\.C)$", "", club, flags=re.IGNORECASE)
    club = re.sub(r"\s+", " ", club)
    return club


def is_valid_player_id(player_id: any) -> bool:
    """Check if player_id is valid."""
    if player_id is None or (isinstance(player_id, float) and player_id != player_id):  # NaN check
        return False
    if isinstance(player_id, str):
        return len(player_id.strip()) > 0
    if isinstance(player_id, int):
        return player_id > 0
    return False


def is_valid_country(country: Optional[str]) -> bool:
    """Check if country is valid."""
    if not country or (isinstance(country, float)):
        return False
    country = str(country).strip()
    return len(country) > 0


def is_valid_position(pos: Optional[str]) -> bool:
    """Check if position is valid."""
    if not pos or (isinstance(pos, float)):
        return False
    pos = str(pos).strip().upper()
    valid_positions = {"GK", "CB", "LB", "RB", "LWB", "RWB", "DM", "CM", "AM", "LM", "RM", "LW", "RW", "CF", "ST", "FW"}
    return pos.split(",")[0].strip() in valid_positions


def is_valid_market_value(value: any) -> bool:
    """Check if market value is valid."""
    try:
        if value is None or (isinstance(value, float) and value != value):
            return True  # Missing is okay
        val = float(value)
        return 0 <= val <= 1_000_000_000
    except (ValueError, TypeError):
        return False


def parse_market_value(value: any) -> Optional[float]:
    """Parse market value from string or number."""
    if value is None or (isinstance(value, float) and value != value):
        return None
    try:
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
            # Handle suffix format (e.g., "€50M" or "50M")
            value = value.replace("€", "").strip()
            if value.endswith("M"):
                return float(value[:-1]) * 1_000_000
            elif value.endswith("K"):
                return float(value[:-1]) * 1_000
            else:
                return float(value)
        return float(value)
    except (ValueError, AttributeError):
        return None


def extract_age_from_date(birth_date: Optional[str]) -> Optional[int]:
    """Extract age from birth date string (YYYY-MM-DD format)."""
    if not birth_date or (isinstance(birth_date, float)):
        return None
    try:
        from datetime import datetime
        birth = datetime.strptime(str(birth_date).strip(), "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
        return age if 16 <= age <= 50 else None
    except (ValueError, AttributeError):
        return None


def validate_row(row_dict: dict, required_fields: List[str]) -> Tuple[bool, List[str]]:
    """Validate a row has all required fields."""
    missing = [field for field in required_fields if field not in row_dict or not row_dict[field]]
    return len(missing) == 0, missing
