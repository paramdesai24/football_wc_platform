"""
Intelligence Data Loader
=========================
Loads all Phase 2 football intelligence datasets and merges them
into a unified team intelligence lookup for match prediction.
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, Any

from .constants import (
    ELO_FILE, ATTACK_DEFENSE_FILE, FORM_FILE, SQUAD_FILE,
    RANKINGS_FILE, COUNTRY_INTEL_FILE, CONFEDERATION_STRENGTH,
    ATTACK_RATING_MEAN, DEFENSE_RATING_MEAN,
)

logger = logging.getLogger("match_engine.data_loader")


class IntelligenceDataLoader:
    """
    Loads and merges all Phase 2 intelligence data into a single
    team-indexed lookup table for the match prediction engine.
    """

    def __init__(self):
        self._elo: Optional[pd.DataFrame] = None
        self._attack_defense: Optional[pd.DataFrame] = None
        self._form: Optional[pd.DataFrame] = None
        self._squad: Optional[pd.DataFrame] = None
        self._rankings: Optional[pd.DataFrame] = None
        self._country_intel: Optional[pd.DataFrame] = None
        self._merged: Optional[pd.DataFrame] = None
        self._team_index: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    # ── public API ────────────────────────────────────────────

    def load_all(self) -> "IntelligenceDataLoader":
        """Load all intelligence datasets and merge them."""
        logger.info("Loading Phase 2 intelligence datasets...")

        self._elo = self._safe_load(ELO_FILE, "Elo ratings")
        self._attack_defense = self._safe_load(ATTACK_DEFENSE_FILE, "Attack/Defense ratings")
        self._form = self._safe_load(FORM_FILE, "Recent form")
        self._squad = self._safe_load(SQUAD_FILE, "Squad strength")
        self._rankings = self._safe_load(RANKINGS_FILE, "World rankings")
        self._country_intel = self._safe_load(COUNTRY_INTEL_FILE, "Country intelligence")

        self._merge_intelligence()
        self._build_team_index()
        self._compute_league_averages()
        self._loaded = True

        logger.info(
            "Intelligence loaded: %d active teams | %d features per team",
            len(self._team_index), len(next(iter(self._team_index.values()), {})),
        )
        return self

    def get_team(self, team_name: str) -> Optional[Dict[str, Any]]:
        """Get intelligence for a single team by name (case-insensitive)."""
        if not self._loaded:
            self.load_all()
        key = team_name.strip().lower()
        return self._team_index.get(key)

    def get_team_by_uid(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get intelligence for a team by country_uid."""
        if not self._loaded:
            self.load_all()
        for data in self._team_index.values():
            if data.get("country_uid") == uid:
                return data
        return None

    def list_teams(self) -> list:
        """Return sorted list of all available team names."""
        if not self._loaded:
            self.load_all()
        return sorted([v["country_name"] for v in self._team_index.values()])

    def get_all_teams_df(self) -> pd.DataFrame:
        """Return merged intelligence as a DataFrame."""
        if not self._loaded:
            self.load_all()
        return self._merged.copy()

    @property
    def league_averages(self) -> Dict[str, float]:
        """League-wide averages for normalization."""
        if not self._loaded:
            self.load_all()
        return self._averages

    @property
    def team_count(self) -> int:
        return len(self._team_index)

    # ── private helpers ───────────────────────────────────────

    def _safe_load(self, path: Path, label: str) -> Optional[pd.DataFrame]:
        """Load a CSV with error handling."""
        try:
            df = pd.read_csv(path)
            logger.info("  [OK] %s: %d rows x %d cols", label, len(df), len(df.columns))
            return df
        except FileNotFoundError:
            logger.warning("  [ERR] %s not found: %s", label, path)
            return None
        except Exception as e:
            logger.error("  [ERR] %s load error: %s", label, e)
            return None

    def _merge_intelligence(self):
        """
        Merge all intelligence sources into a single DataFrame.

        IMPORTANT: Specialized source files (elo, attack_defense, form, squad)
        ALWAYS take priority over the rankings base table. The rankings file
        may contain placeholder values for these columns — we must overwrite
        them with the real data from the specialized sources.
        """
        # Start with rankings as the base (has the most columns)
        base = self._rankings.copy() if self._rankings is not None else pd.DataFrame()

        if base.empty and self._elo is not None:
            base = self._elo.copy()

        if base.empty:
            raise RuntimeError("No intelligence data available. Run Phase 2 first.")

        merge_key = "country_uid"

        # ── Elo ratings: ALWAYS prefer specialized source ──
        if self._elo is not None and merge_key in self._elo.columns:
            elo_cols = [c for c in ["elo_rating"] if c in self._elo.columns]
            # Drop existing columns from base so we use the real source
            base = base.drop(columns=[c for c in elo_cols if c in base.columns], errors="ignore")
            base = base.merge(
                self._elo[[merge_key] + elo_cols], on=merge_key, how="left", suffixes=("", "_elo")
            )

        # ── Attack/Defense ratings: ALWAYS prefer specialized source ──
        if self._attack_defense is not None and merge_key in self._attack_defense.columns:
            ad_cols = [c for c in ["attack_rating", "defense_rating"] if c in self._attack_defense.columns]
            base = base.drop(columns=[c for c in ad_cols if c in base.columns], errors="ignore")
            base = base.merge(
                self._attack_defense[[merge_key] + ad_cols], on=merge_key, how="left", suffixes=("", "_ad")
            )

        # ── Form data: ALWAYS prefer specialized source ──
        if self._form is not None and merge_key in self._form.columns:
            form_cols = [c for c in ["recent_form_score", "momentum_score",
                         "consistency_score", "streak_score"] if c in self._form.columns]
            base = base.drop(columns=[c for c in form_cols if c in base.columns], errors="ignore")
            base = base.merge(
                self._form[[merge_key] + form_cols], on=merge_key, how="left", suffixes=("", "_form")
            )

        # ── Squad strength: ALWAYS prefer specialized source ──
        if self._squad is not None and merge_key in self._squad.columns:
            squad_cols = [c for c in ["squad_overall_strength", "squad_attack_score",
                          "squad_defense_score", "squad_depth_score", "squad_form_score",
                          "squad_experience_score", "squad_confidence"] if c in self._squad.columns]
            base = base.drop(columns=[c for c in squad_cols if c in base.columns], errors="ignore")
            base = base.merge(
                self._squad[[merge_key] + squad_cols], on=merge_key, how="left", suffixes=("", "_sq")
            )

        # Filter to prediction-eligible teams only
        if "prediction_eligible" in base.columns:
            base = base[base["prediction_eligible"] == True].copy()

        # Fill NaN with sensible defaults
        if "elo_rating" in base.columns:
            base["elo_rating"] = base["elo_rating"].fillna(1500.0)
        numeric_cols = base.select_dtypes(include=[np.number]).columns
        base[numeric_cols] = base[numeric_cols].fillna(base[numeric_cols].median())

        self._merged = base.reset_index(drop=True)
        logger.info("  Merged intelligence: %d teams x %d features", len(self._merged), len(self._merged.columns))

    def _build_team_index(self):
        """Build a fast name→data lookup dictionary."""
        self._team_index = {}
        for _, row in self._merged.iterrows():
            name = str(row.get("country_name", "")).strip()
            if not name:
                continue
            entry = row.to_dict()
            # Add confederation strength
            conf = entry.get("confederation", "")
            entry["confederation_strength"] = CONFEDERATION_STRENGTH.get(conf, 0.50)
            self._team_index[name.lower()] = entry

    def _compute_league_averages(self):
        """Compute league-wide averages for normalization."""
        df = self._merged
        self._averages = {
            "elo_rating": df["elo_rating"].mean() if "elo_rating" in df.columns else 1500,
            "attack_rating": df["attack_rating"].mean() if "attack_rating" in df.columns else ATTACK_RATING_MEAN,
            "defense_rating": df["defense_rating"].mean() if "defense_rating" in df.columns else DEFENSE_RATING_MEAN,
            "recent_form_score": df["recent_form_score"].mean() if "recent_form_score" in df.columns else 0.5,
            "squad_overall_strength": df["squad_overall_strength"].mean() if "squad_overall_strength" in df.columns else 0.5,
            "overall_rank_score": df["overall_rank_score"].mean() if "overall_rank_score" in df.columns else 0.5,
        }
        logger.info(
            "  League averages — Elo: %.0f | Attack: %.1f | Defense: %.1f | Form: %.3f",
            self._averages["elo_rating"], self._averages["attack_rating"],
            self._averages["defense_rating"], self._averages["recent_form_score"],
        )
