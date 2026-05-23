"""Utilities for rendering country flags and team display names.

Provides a lightweight, deployment-safe way to show Unicode emoji
flags generated from ISO alpha-2 country codes and a central team->ISO map.
"""
from __future__ import annotations

import re
from typing import Dict, Optional


def country_code_to_flag(code: str) -> str:
    """Convert an ISO alpha-2 country code (e.g. 'BR') to a Unicode flag emoji."""
    if not code or not isinstance(code, str):
        return ""
    code = code.strip().upper()
    if len(code) != 2 or not code.isalpha():
        return ""
    return "".join(chr(127397 + ord(c)) for c in code)


# Centralized mapping from canonical team/country display name to ISO alpha-2.
# Keep this mapping authoritative and reusable across the app.
TEAM_TO_ISO: Dict[str, str] = {
    "Argentina": "AR",
    "Australia": "AU",
    "Belgium": "BE",
    "Brazil": "BR",
    "Canada": "CA",
    "Costa Rica": "CR",
    "Mexico": "MX",
    "United States": "US",
    "USA": "US",
    "United States of America": "US",
    "England": "GB",
    "France": "FR",
    "Germany": "DE",
    "Italy": "IT",
    "Netherlands": "NL",
    "Spain": "ES",
    "Portugal": "PT",
    "Uruguay": "UY",
    "Colombia": "CO",
    "Morocco": "MA",
    "Japan": "JP",
    "South Korea": "KR",
    "Korea Republic": "KR",
    "South Korea Republic": "KR",
    "Senegal": "SN",
    "Switzerland": "CH",
    "Denmark": "DK",
    "Sweden": "SE",
    "Norway": "NO",
    "Poland": "PL",
    "Austria": "AT",
    "Croatia": "HR",
    "Serbia": "RS",
    "Turkey": "TR",
    "Egypt": "EG",
    "Tunisia": "TN",
    "Algeria": "DZ",
    "Nigeria": "NG",
    "Ghana": "GH",
    "Cameroon": "CM",
    "Ivory Coast": "CI",
    "Côte d'Ivoire": "CI",
    "Scotland": "GB",
    "Wales": "GB",
    "Northern Ireland": "GB",
    "Ireland": "IE",
    "Haiti": "HT",
    "Qatar": "QA",
    "Bosnia and Herzegovina": "BA",
    "Honduras": "HN",
    "New Zealand": "NZ",
    "Iceland": "IS",
    "South Africa": "ZA",
    "Zimbabwe": "ZW",
    "Chile": "CL",
    "Peru": "PE",
    "Ecuador": "EC",
    "Venezuela": "VE",
    "Panama": "PA",
    "Paraguay": "PY",
    "Bolivia": "BO",
    "El Salvador": "SV",
    "Guatemala": "GT",
    "Jamaica": "JM",
    "Trinidad and Tobago": "TT",
    # Add more mappings as needed; fallback to team name when missing.
}

ISO_TO_TEAM: Dict[str, str] = {iso: team for team, iso in TEAM_TO_ISO.items()}

TEAM_ALIASES: Dict[str, list[str]] = {
    "Argentina": ["ARG"],
    "Australia": ["AUS"],
    "Belgium": ["BEL"],
    "Brazil": ["BRA"],
    "Canada": ["CAN"],
    "Colombia": ["COL"],
    "Denmark": ["DEN"],
    "England": ["ENG"],
    "France": ["FRA"],
    "Germany": ["GER"],
    "Italy": ["ITA"],
    "Japan": ["JPN"],
    "Mexico": ["MEX"],
    "Morocco": ["MOR"],
    "Netherlands": ["NED"],
    "Portugal": ["POR"],
    "South Korea": ["KOR"],
    "Spain": ["ESP"],
    "Switzerland": ["SUI"],
    "United States": ["USA"],
    "Uruguay": ["URU"],
}

ALIAS_TO_TEAM: Dict[str, str] = {
    alias: team for team, aliases in TEAM_ALIASES.items() for alias in aliases
}


def normalize_country_display(text: Optional[str]) -> str:
    """Replace common football country tokens in free text with flag + team name."""
    if not text:
        return ""

    value = str(text)
    placeholders: Dict[str, str] = {}
    placeholder_index = 0

    def stash_display(display_text: str) -> str:
        nonlocal placeholder_index
        placeholder = f"@@TEAM_{placeholder_index}@@"
        placeholder_index += 1
        placeholders[placeholder] = display_text
        return placeholder

    # First collapse combined forms like "BRA Brazil" or "BR Brazil" into one
    # formatted display, then replace standalone aliases/codes.
    for team, aliases in TEAM_ALIASES.items():
        combined = rf"(?:{'|'.join(re.escape(alias) for alias in aliases)}|{re.escape(TEAM_TO_ISO.get(team, ''))})\s+{re.escape(team)}"
        value = re.sub(combined, stash_display(format_team_display(team)), value)

    tokens = sorted(set(list(TEAM_TO_ISO.keys()) + list(ALIAS_TO_TEAM.keys()) + list(ISO_TO_TEAM.keys())), key=len, reverse=True)
    if tokens:
        pattern = rf"(?<![A-Za-z])({'|'.join(re.escape(token) for token in tokens)})(?![A-Za-z])"

        def replace_token(match: re.Match[str]) -> str:
            token = match.group(1)
            team = TEAM_TO_ISO.get(token)
            if team:
                return format_team_display(token)
            alias_team = ALIAS_TO_TEAM.get(token.upper())
            if alias_team:
                return format_team_display(alias_team)
            iso_team = ISO_TO_TEAM.get(token.upper())
            if iso_team:
                return format_team_display(iso_team)
            return token

        value = re.sub(pattern, replace_token, value)

    for placeholder, display_text in placeholders.items():
        value = value.replace(placeholder, display_text)

    return value


def format_team_display(team_name: Optional[str]) -> str:
    """Return a display string with flag emoji and full team name.

    Accepts either a full team name (e.g. "Brazil") or a raw ISO alpha-2 code
    (e.g. "BR") and always returns a plain UTF-8 string.
    """
    if not team_name:
        return ""
    name = str(team_name).strip()
    iso = TEAM_TO_ISO.get(name)
    if iso:
        flag = country_code_to_flag(iso)
        return f"{flag} {name}"

    if len(name) == 2 and name.isalpha():
        team = ISO_TO_TEAM.get(name.upper())
        if team:
            flag = country_code_to_flag(name)
            return f"{flag} {team}"

    alias_team = ALIAS_TO_TEAM.get(name.upper())
    if alias_team:
        iso = TEAM_TO_ISO.get(alias_team)
        flag = country_code_to_flag(iso) if iso else ""
        return f"{flag} {alias_team}".strip()

    # Fallback to a plain team name if we cannot map it.
    if name.upper() in ISO_TO_TEAM:
        team = ISO_TO_TEAM[name.upper()]
        flag = country_code_to_flag(name)
        return f"{flag} {team}"
    return name
