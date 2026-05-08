"""Aggregate country-level metrics and merge with squad aggregates."""

import pandas as pd
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class CountryAggregator:
    """Aggregate results into country intelligence metrics."""

    @staticmethod
    def create_country_metrics(results: pd.DataFrame) -> pd.DataFrame:
        """Create country metrics (wins, draws, losses, goals, conceded, win_rate)."""
        if results is None or results.empty:
            logger.warning("No results provided to CountryAggregator")
            return pd.DataFrame()

        logger.info("Calculating country-level match statistics...")

        # Ensure columns
        cols = results.columns
        home_cols = [c for c in ["home_team", "home_score"] if c in cols]
        away_cols = [c for c in ["away_team", "away_score"] if c in cols]

        # Home stats
        home = results[["home_team", "home_score", "away_score"]].copy()
        home.columns = ["country", "goals_for", "goals_against"]
        away = results[["away_team", "away_score", "home_score"]].copy()
        away.columns = ["country", "goals_for", "goals_against"]

        concat = pd.concat([home, away], ignore_index=True)

        grp = concat.groupby("country").agg(
            total_matches=("goals_for", "count"),
            goals_for=("goals_for", "sum"),
            goals_against=("goals_against", "sum"),
        ).reset_index()

        # Win/draw/loss require original results
        def compute_wdl(df, team_col_prefix):
            wins = []
            draws = []
            losses = []
            countries = []
            for country, group in df.groupby(team_col_prefix):
                countries.append(country)
                w = 0
                d = 0
                l = 0
                for _, row in group.iterrows():
                    home = row.get("home_team")
                    away = row.get("away_team")
                    hs = row.get("home_score")
                    as_ = row.get("away_score")
                    if home == country:
                        if hs > as_:
                            w += 1
                        elif hs == as_:
                            d += 1
                        else:
                            l += 1
                    elif away == country:
                        if as_ > hs:
                            w += 1
                        elif as_ == hs:
                            d += 1
                        else:
                            l += 1
                wins.append(w)
                draws.append(d)
                losses.append(l)
            return pd.DataFrame({"country": countries, "wins": wins, "draws": draws, "losses": losses})

        wdl = compute_wdl(results, "home_team")

        merged = grp.merge(wdl, on="country", how="left").fillna(0)
        merged["win_rate"] = merged.apply(lambda r: (r["wins"] / r["total_matches"]) if r["total_matches"] > 0 else 0, axis=1)

        logger.info(f"✓ Calculated country metrics for {len(merged)} countries")
        return merged
