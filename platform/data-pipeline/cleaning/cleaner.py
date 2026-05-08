"""
Data cleaning pipelines.
"""

import pandas as pd
import logging
from typing import Optional, List
from utils.normalization import (
    normalize_string, normalize_player_name, normalize_country,
    normalize_position, normalize_club_name, is_valid_player_id,
    is_valid_country, parse_market_value
)

logger = logging.getLogger(__name__)


class DataCleaner:
    """Data cleaning pipelines."""
    
    @staticmethod
    def clean_players(df: pd.DataFrame) -> pd.DataFrame:
        """Clean players dataset."""
        df = df.copy()
        logger.info(f"Cleaning players dataset: {len(df)} rows")
        
        # Normalize names
        if "player_name" in df.columns:
            df["player_name"] = df["player_name"].apply(normalize_player_name)
        
        # Normalize country
        if "country_of_citizenship" in df.columns:
            df["country_of_citizenship"] = df["country_of_citizenship"].apply(normalize_country)
        
        # Normalize position
        if "position" in df.columns:
            df["position"] = df["position"].apply(normalize_position)
        
        # Clean birth_date
        if "date_of_birth" in df.columns:
            df["date_of_birth"] = pd.to_datetime(df["date_of_birth"], errors="coerce")
        
        # Remove duplicates by player_id
        if "player_id" in df.columns:
            df = df.drop_duplicates(subset=["player_id"], keep="first")
        
        logger.info(f"✓ Cleaned players: {len(df)} rows remaining")
        return df
    
    @staticmethod
    def clean_valuations(df: pd.DataFrame) -> pd.DataFrame:
        """Clean player valuations dataset."""
        df = df.copy()
        logger.info(f"Cleaning valuations dataset: {len(df)} rows")
        
        # Parse market value
        if "market_value_in_eur" in df.columns:
            df["market_value_in_eur"] = df["market_value_in_eur"].apply(parse_market_value)
        
        # Convert date
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        
        # Remove nulls
        df = df.dropna(subset=["player_id", "market_value_in_eur"])
        
        logger.info(f"✓ Cleaned valuations: {len(df)} rows remaining")
        return df
    
    @staticmethod
    def clean_appearances(df: pd.DataFrame) -> pd.DataFrame:
        """Clean appearances dataset."""
        df = df.copy()
        logger.info(f"Cleaning appearances dataset: {len(df)} rows")
        
        # Convert date
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        
        # Numeric columns
        numeric_cols = ["goals", "assists", "minutes_played"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        # Remove nulls
        df = df.dropna(subset=["player_id", "game_id"])
        
        logger.info(f"✓ Cleaned appearances: {len(df)} rows remaining")
        return df
    
    @staticmethod
    def clean_games(df: pd.DataFrame) -> pd.DataFrame:
        """Clean games dataset."""
        df = df.copy()
        logger.info(f"Cleaning games dataset: {len(df)} rows")
        
        # Convert date
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        
        # Numeric columns
        numeric_cols = ["home_club_goals", "away_club_goals"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        # Remove nulls
        df = df.dropna(subset=["game_id"])
        
        logger.info(f"✓ Cleaned games: {len(df)} rows remaining")
        return df
    
    @staticmethod
    def clean_results(df: pd.DataFrame) -> pd.DataFrame:
        """Clean international results dataset."""
        df = df.copy()
        logger.info(f"Cleaning results dataset: {len(df)} rows")
        
        # Normalize countries
        if "home_team" in df.columns:
            df["home_team"] = df["home_team"].apply(normalize_country)
        if "away_team" in df.columns:
            df["away_team"] = df["away_team"].apply(normalize_country)
        
        # Convert date
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        
        # Numeric columns
        numeric_cols = ["home_score", "away_score"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
        # Remove nulls
        df = df.dropna(subset=["home_team", "away_team", "date"])
        
        logger.info(f"✓ Cleaned results: {len(df)} rows remaining")
        return df
    
    @staticmethod
    def clean_clubs(df: pd.DataFrame) -> pd.DataFrame:
        """Clean clubs dataset."""
        df = df.copy()
        logger.info(f"Cleaning clubs dataset: {len(df)} rows")
        
        # Normalize names
        if "club_name" in df.columns:
            df["club_name"] = df["club_name"].apply(normalize_club_name)
        
        if "country_id" in df.columns:
            # Keep country codes as-is
            pass
        
        logger.info(f"✓ Cleaned clubs: {len(df)} rows remaining")
        return df
