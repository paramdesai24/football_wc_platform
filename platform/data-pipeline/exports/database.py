"""
SQLite database integration for football intelligence data.
"""

import sqlite3
import pandas as pd
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class FootballIntelligenceDB:
    """SQLite database for storing processed intelligence datasets."""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.connection = None
        self.ensure_connected()
    
    def ensure_connected(self) -> None:
        """Ensure database connection is active."""
        if self.connection is None:
            try:
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
                self.connection = sqlite3.connect(str(self.db_path))
                logger.info(f"✓ Connected to database: {self.db_path}")
            except Exception as e:
                logger.error(f"Failed to connect to database: {e}")
                raise
    
    def close(self) -> None:
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")
    
    def create_tables(self) -> None:
        """Create all necessary tables."""
        logger.info("Creating database tables...")
        
        cursor = self.connection.cursor()

        # Required Phase 1 tables (canonical names)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS master_players (
                player_id TEXT PRIMARY KEY,
                name TEXT,
                country TEXT,
                club TEXT,
                position TEXT,
                age INTEGER,
                market_value REAL,
                goals INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                minutes_played INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                goals_per_90 REAL,
                assists_per_90 REAL,
                contribution_per_90 REAL,
                form_score REAL,
                consistency_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS master_countries (
                country TEXT PRIMARY KEY,
                confederation TEXT,
                total_matches INTEGER,
                wins INTEGER,
                draws INTEGER,
                losses INTEGER,
                win_rate REAL,
                goals_for INTEGER,
                goals_against INTEGER,
                goals_per_match REAL,
                conceded_per_match REAL,
                attack_rating REAL,
                defense_rating REAL,
                elo_rating REAL,
                historical_strength REAL,
                recent_form_score REAL,
                power_index REAL,
                power_rank INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS player_form (
                player_id TEXT PRIMARY KEY,
                goals INTEGER,
                assists INTEGER,
                minutes_played INTEGER,
                games_played INTEGER,
                goals_per_90 REAL,
                assists_per_90 REAL,
                contribution_per_90 REAL,
                form_score REAL,
                consistency_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS country_strength (
                country TEXT PRIMARY KEY,
                total_matches INTEGER,
                wins INTEGER,
                draws INTEGER,
                losses INTEGER,
                win_rate REAL,
                goals_for INTEGER,
                goals_against INTEGER,
                goals_per_match REAL,
                conceded_per_match REAL,
                goal_differential REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Players table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                country TEXT,
                club TEXT,
                position TEXT,
                age INTEGER,
                market_value REAL,
                goals INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                minutes_played INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                goals_per_90 REAL,
                assists_per_90 REAL,
                contribution_per_90 REAL,
                form_score REAL,
                consistency_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Countries table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS countries (
                country TEXT PRIMARY KEY,
                confederation TEXT,
                total_matches INTEGER,
                wins INTEGER,
                draws INTEGER,
                losses INTEGER,
                win_rate REAL,
                goals_for INTEGER,
                goals_against INTEGER,
                goals_per_match REAL,
                conceded_per_match REAL,
                attack_rating REAL,
                defense_rating REAL,
                elo_rating REAL,
                historical_strength REAL,
                recent_form_score REAL,
                power_index REAL,
                power_rank INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Squad aggregates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS squad_aggregates (
                country TEXT PRIMARY KEY,
                squad_size INTEGER,
                total_market_value REAL,
                avg_player_value REAL,
                avg_goals_per_90 REAL,
                avg_assists_per_90 REAL,
                avg_form_score REAL,
                avg_consistency_score REAL,
                squad_strength REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Audit metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                step_name TEXT NOT NULL,
                status TEXT,
                records_processed INTEGER,
                records_created INTEGER,
                execution_time_seconds REAL,
                executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.connection.commit()
        logger.info("✓ Created all database tables")

    def _write_table(self, table_name: str, df: pd.DataFrame, replace: bool = True) -> int:
        try:
            method = "replace" if replace else "append"
            df.to_sql(table_name, self.connection, if_exists=method, index=False)
            logger.info(f"Inserted {len(df)} rows into {table_name}")
            return len(df)
        except Exception as e:
            logger.error(f"Failed to insert into {table_name}: {e}")
            return 0
    
    def insert_players(self, df: pd.DataFrame, replace: bool = True) -> int:
        """Insert or replace players data."""
        return self._write_table("players", df, replace)

    def insert_master_players(self, df: pd.DataFrame, replace: bool = True) -> int:
        """Insert or replace master players data."""
        return self._write_table("master_players", df, replace)
    
    def insert_countries(self, df: pd.DataFrame, replace: bool = True) -> int:
        """Insert or replace countries data."""
        return self._write_table("countries", df, replace)

    def insert_master_countries(self, df: pd.DataFrame, replace: bool = True) -> int:
        """Insert or replace master countries data."""
        return self._write_table("master_countries", df, replace)

    def insert_player_form(self, df: pd.DataFrame, replace: bool = True) -> int:
        """Insert or replace player form data."""
        return self._write_table("player_form", df, replace)

    def insert_country_strength(self, df: pd.DataFrame, replace: bool = True) -> int:
        """Insert or replace country strength data."""
        return self._write_table("country_strength", df, replace)
    
    def insert_squad_aggregates(self, df: pd.DataFrame, replace: bool = True) -> int:
        """Insert or replace squad aggregates."""
        try:
            method = "replace" if replace else "append"
            df.to_sql("squad_aggregates", self.connection, if_exists=method, index=False)
            logger.info(f"✓ Inserted {len(df)} squad aggregates into database")
            return len(df)
        except Exception as e:
            logger.error(f"Failed to insert squad aggregates: {e}")
            return 0
    
    def log_pipeline_step(
        self,
        step_name: str,
        status: str,
        records_processed: int,
        records_created: int,
        execution_time: float,
    ) -> None:
        """Log pipeline execution step."""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                INSERT INTO pipeline_metadata 
                (step_name, status, records_processed, records_created, execution_time_seconds)
                VALUES (?, ?, ?, ?, ?)
            """, (step_name, status, records_processed, records_created, execution_time))
            self.connection.commit()
        except Exception as e:
            logger.error(f"Failed to log pipeline step: {e}")
    
    def query(self, sql: str) -> pd.DataFrame:
        """Execute a query and return results as DataFrame."""
        try:
            return pd.read_sql_query(sql, self.connection)
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return pd.DataFrame()
    
    def get_players(self) -> pd.DataFrame:
        """Get all players from database."""
        return self.query("SELECT * FROM players")
    
    def get_countries(self) -> pd.DataFrame:
        """Get all countries from database."""
        return self.query("SELECT * FROM countries")
    
    def get_squad_aggregates(self) -> pd.DataFrame:
        """Get all squad aggregates from database."""
        return self.query("SELECT * FROM squad_aggregates")
