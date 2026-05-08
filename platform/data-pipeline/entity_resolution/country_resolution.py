"""
Country Resolution: Canonicalize countries and resolve naming inconsistencies.

Handles:
- Country name normalization
- Canonical country UID generation
- Historical country name mapping
- Confederation assignment
"""

import pandas as pd
import hashlib
from typing import Dict, Optional
import logging
from utils.entity_registry import canonicalize_country, get_country_iso2

logger = logging.getLogger(__name__)


class CountryResolver:
    """
    Resolve country entities and generate canonical identifiers.
    """

    def __init__(self):
        self.country_uid_map = {}  # canonical_name -> country_uid
        self.country_iso_map = {}  # canonical_name -> ISO2

    def generate_country_uid(self, country_name: str) -> str:
        """
        Generate canonical country UID.

        Args:
            country_name: Input country name

        Returns:
            Stable country UID (e.g., C_ARG, C_BRA)
        """
        canonical = canonicalize_country(country_name)
        if not canonical:
            canonical = country_name

        if canonical in self.country_uid_map:
            return self.country_uid_map[canonical]

        iso2 = get_country_iso2(canonical)
        if iso2:
            country_uid = f"C_{iso2.upper()}"
        else:
            # Fallback: use first 3 letters
            country_uid = f"C_{canonical[:3].upper()}"

        self.country_uid_map[canonical] = country_uid
        return country_uid

    def add_country_uid(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add canonical country_uid column to DataFrame.

        Assumes 'country' or 'name' column exists.
        """
        df = df.copy()

        if "country" in df.columns:
            country_col = "country"
        elif "name" in df.columns:
            country_col = "name"
        else:
            logger.warning("No country/name column found")
            return df

        df["country_uid"] = df[country_col].apply(self.generate_country_uid)

        return df

    def canonicalize_countries(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Canonicalize country names in DataFrame.

        Applies mapping to 'country', 'home_team', 'away_team', etc. columns.
        """
        df = df.copy()

        country_columns = [col for col in df.columns if "country" in col.lower() or "team" in col.lower()]

        for col in country_columns:
            if df[col].dtype == "object":
                df[col] = df[col].apply(canonicalize_country)

        return df

    def deduplicate_countries(self, countries_df: pd.DataFrame) -> pd.DataFrame:
        """
        Remove duplicate country records, keeping first occurrence.
        """
        if "country_uid" not in countries_df.columns:
            countries_df = self.add_country_uid(countries_df)

        deduplicated = countries_df.drop_duplicates(subset=["country_uid"], keep="first")

        logger.info(f"Deduplicated countries: {len(countries_df)} → {len(deduplicated)}")

        return deduplicated

    def add_confederation(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add confederation assignment based on country.

        Confederation mapping:
        - CONMEBOL: South American countries
        - UEFA: European countries
        - CAF: African countries
        - AFC: Asian countries
        - CONCACAF: North American countries
        - OFC: Oceania countries
        """
        confederation_map = {
            "Argentina": "CONMEBOL",
            "Brazil": "CONMEBOL",
            "Chile": "CONMEBOL",
            "Colombia": "CONMEBOL",
            "Ecuador": "CONMEBOL",
            "Paraguay": "CONMEBOL",
            "Peru": "CONMEBOL",
            "Uruguay": "CONMEBOL",
            "Venezuela": "CONMEBOL",
            "Bolivia": "CONMEBOL",
            "France": "UEFA",
            "Germany": "UEFA",
            "England": "UEFA",
            "Spain": "UEFA",
            "Italy": "UEFA",
            "Netherlands": "UEFA",
            "Belgium": "UEFA",
            "Portugal": "UEFA",
            "Denmark": "UEFA",
            "Sweden": "UEFA",
            "Norway": "UEFA",
            "Poland": "UEFA",
            "Ukraine": "UEFA",
            "Russia": "UEFA",
            "Czechia": "UEFA",
            "Wales": "UEFA",
            "Scotland": "UEFA",
            "Northern Ireland": "UEFA",
            "Ireland": "UEFA",
            "Egypt": "CAF",
            "Nigeria": "CAF",
            "Cameroon": "CAF",
            "South Africa": "CAF",
            "Algeria": "CAF",
            "Morocco": "CAF",
            "Tunisia": "CAF",
            "Senegal": "CAF",
            "Ghana": "CAF",
            "Côte d'Ivoire": "CAF",
            "Japan": "AFC",
            "South Korea": "AFC",
            "China": "AFC",
            "India": "AFC",
            "Saudi Arabia": "AFC",
            "Qatar": "AFC",
            "United Arab Emirates": "AFC",
            "Iran": "AFC",
            "Australia": "AFC",
            "Mexico": "CONCACAF",
            "United States": "CONCACAF",
            "Canada": "CONCACAF",
            "Costa Rica": "CONCACAF",
            "Honduras": "CONCACAF",
            "Panama": "CONCACAF",
            "Jamaica": "CONCACAF",
            "Trinidad and Tobago": "CONCACAF",
            "New Zealand": "OFC",
            "Fiji": "OFC",
            "Samoa": "OFC",
        }

        df = df.copy()

        if "country" in df.columns:
            country_col = "country"
        elif "name" in df.columns:
            country_col = "name"
        else:
            return df

        df["confederation"] = df[country_col].map(confederation_map)

        return df

    def resolve_countries(self, countries_df: pd.DataFrame) -> pd.DataFrame:
        """
        Full country resolution pipeline:
        1. Canonicalize names
        2. Generate UIDs
        3. Deduplicate
        4. Add confederation
        """
        logger.info(f"Starting country resolution for {len(countries_df)} records")

        # Canonicalize
        countries_df = self.canonicalize_countries(countries_df)

        # Generate UIDs
        countries_df = self.add_country_uid(countries_df)

        # Deduplicate
        countries_df = self.deduplicate_countries(countries_df)

        # Add confederation
        countries_df = self.add_confederation(countries_df)

        logger.info(f"✓ Country resolution complete: {len(countries_df)} countries with UIDs")

        return countries_df
