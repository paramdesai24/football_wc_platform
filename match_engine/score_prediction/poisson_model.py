"""
Poisson Score Model — v2.0
============================
Football-realistic scoreline prediction using Poisson distribution
with Dixon-Coles correction for draw suppression.

Key changes from v1:
- Dixon-Coles low-score adjustment (suppresses 0-0/1-1 dominance)
- Expanded matrix to 0-7 goals
- Context-aware predicted scoreline (not just max cell)
- Better scoreline diversity
"""

import logging
import numpy as np
from scipy.stats import poisson
from typing import Dict, Any, List, Tuple

from ..utils.constants import (
    MAX_SCORELINE, MIN_REALISTIC_XG, MAX_REALISTIC_XG,
    DIXON_COLES_RHO,
)
from ..utils.helpers import clamp

logger = logging.getLogger("match_engine.poisson_model")


class PoissonScoreModel:
    """
    Poisson-based scoreline prediction with Dixon-Coles correction.

    The standard independent Poisson model over-predicts draws because
    it ignores the negative correlation between goals in low-scoring matches.
    Dixon-Coles (1997) corrects this by adjusting the 0-0, 1-0, 0-1, and
    1-1 cells with a correlation parameter rho.
    """

    def __init__(self, max_goals: int = MAX_SCORELINE, rho: float = DIXON_COLES_RHO):
        self.max_goals = max_goals
        self.rho = rho  # Negative rho suppresses draws

    def predict(
        self,
        home_xg: float,
        away_xg: float,
        home_name: str = "Home",
        away_name: str = "Away",
    ) -> Dict[str, Any]:
        """
        Generate scoreline predictions from expected goals.

        Returns dict with score_matrix, top_scorelines, predicted_score,
        match_outcome_probs, and market probabilities.
        """
        home_xg = clamp(home_xg, MIN_REALISTIC_XG, MAX_REALISTIC_XG)
        away_xg = clamp(away_xg, MIN_REALISTIC_XG, MAX_REALISTIC_XG)

        # 1. Build probability matrix with Dixon-Coles adjustment
        matrix = self._build_score_matrix(home_xg, away_xg)

        # 2. Extract top scorelines
        top_scores = self._get_top_scorelines(matrix, home_name, away_name, n=10)

        # 3. Context-aware predicted scoreline
        best_h, best_a = self._select_predicted_score(matrix, home_xg, away_xg)
        predicted_score = f"{home_name} {best_h}-{best_a} {away_name}"

        # 4. Match outcome probabilities from score matrix
        outcome_probs = self._outcome_from_matrix(matrix)

        # 5. Market probabilities
        markets = self._market_probabilities(matrix, home_xg, away_xg)

        return {
            "predicted_score": predicted_score,
            "home_goals": best_h,
            "away_goals": best_a,
            "score_probability": round(float(matrix[best_h, best_a]), 4),
            "top_scorelines": top_scores,
            "outcome_probs": outcome_probs,
            "markets": markets,
            "home_xg": home_xg,
            "away_xg": away_xg,
        }

    def _build_score_matrix(self, home_xg: float, away_xg: float) -> np.ndarray:
        """
        Build NxN probability matrix using independent Poisson distributions
        with Dixon-Coles low-score correction.
        """
        n = self.max_goals + 1
        home_probs = poisson.pmf(np.arange(n), home_xg)
        away_probs = poisson.pmf(np.arange(n), away_xg)
        matrix = np.outer(home_probs, away_probs)

        # Dixon-Coles correction for low-scoring cells
        rho = self.rho
        mu_h = home_xg
        mu_a = away_xg

        # Tau function adjustments (Dixon & Coles, 1997)
        # tau(0,0) = 1 - mu_h * mu_a * rho
        # tau(1,0) = 1 + mu_a * rho
        # tau(0,1) = 1 + mu_h * rho
        # tau(1,1) = 1 - rho
        if n > 1:
            matrix[0, 0] *= max(1.0 - mu_h * mu_a * rho, 0.001)
            matrix[1, 0] *= max(1.0 + mu_a * rho, 0.001)
            matrix[0, 1] *= max(1.0 + mu_h * rho, 0.001)
            matrix[1, 1] *= max(1.0 - rho, 0.001)

        # Ensure non-negative and normalize
        matrix = np.maximum(matrix, 0.0)
        total = matrix.sum()
        if total > 0:
            matrix /= total

        return matrix

    def _select_predicted_score(
        self, matrix: np.ndarray, home_xg: float, away_xg: float
    ) -> Tuple[int, int]:
        """
        Context-aware scoreline selection.

        Instead of always picking the single highest cell (which biases
        toward draws), this method considers:
        1. The xG gap between teams
        2. Cluster analysis of nearby scorelines
        3. Favors decisive outcomes when one team is clearly stronger
        """
        n = matrix.shape[0]

        # Get the raw most-likely score
        raw_best = np.unravel_index(np.argmax(matrix), matrix.shape)
        raw_h, raw_a = int(raw_best[0]), int(raw_best[1])

        xg_gap = home_xg - away_xg

        # If xG gap is significant (>0.3), prefer a decisive scoreline
        if abs(xg_gap) > 0.3:
            # Find the best NON-DRAW scoreline
            best_decisive_prob = 0.0
            best_decisive = (raw_h, raw_a)

            for i in range(n):
                for j in range(n):
                    if i == j:
                        continue  # Skip draws
                    # Only consider scorelines favoring the stronger team
                    if xg_gap > 0 and i <= j:
                        continue  # Home is stronger, skip away wins
                    if xg_gap < 0 and j <= i:
                        continue  # Away is stronger, skip home wins

                    if matrix[i, j] > best_decisive_prob:
                        best_decisive_prob = matrix[i, j]
                        best_decisive = (i, j)

            # Use decisive if its probability is within 70% of the draw cell
            if best_decisive_prob >= matrix[raw_h, raw_a] * 0.65:
                return best_decisive

        # If xG gap is moderate (0.15-0.3), check if the best non-draw
        # is close in probability to the best draw
        if abs(xg_gap) > 0.15:
            best_nondraw_prob = 0.0
            best_nondraw = (raw_h, raw_a)
            for i in range(n):
                for j in range(n):
                    if i != j and matrix[i, j] > best_nondraw_prob:
                        best_nondraw_prob = matrix[i, j]
                        best_nondraw = (i, j)

            if best_nondraw_prob >= matrix[raw_h, raw_a] * 0.85:
                return best_nondraw

        return raw_h, raw_a

    def _most_likely_score(self, matrix: np.ndarray) -> Tuple[int, int]:
        """Find the most probable scoreline (raw, without context)."""
        idx = np.unravel_index(np.argmax(matrix), matrix.shape)
        return int(idx[0]), int(idx[1])

    def _get_top_scorelines(
        self, matrix: np.ndarray, home_name: str, away_name: str, n: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top N most likely scorelines with probabilities."""
        flat = matrix.flatten()
        top_indices = np.argsort(flat)[::-1][:n]
        results = []
        for idx in top_indices:
            h, a = divmod(idx, matrix.shape[1])
            prob = float(flat[idx])
            results.append({
                "scoreline": f"{home_name} {h}-{a} {away_name}",
                "home_goals": int(h),
                "away_goals": int(a),
                "probability": round(prob, 4),
            })
        return results

    def _outcome_from_matrix(self, matrix: np.ndarray) -> Dict[str, float]:
        """Derive win/draw/loss from score matrix."""
        n = matrix.shape[0]
        home_win = 0.0
        draw = 0.0
        away_win = 0.0
        for i in range(n):
            for j in range(n):
                if i > j:
                    home_win += matrix[i, j]
                elif i == j:
                    draw += matrix[i, j]
                else:
                    away_win += matrix[i, j]
        return {
            "home_win": round(home_win, 4),
            "draw": round(draw, 4),
            "away_win": round(away_win, 4),
        }

    def _market_probabilities(
        self, matrix: np.ndarray, home_xg: float, away_xg: float
    ) -> Dict[str, float]:
        """Compute common football betting market probabilities."""
        n = matrix.shape[0]
        total_goals_probs = {}
        for total in range(2 * n):
            prob = 0.0
            for i in range(min(total + 1, n)):
                j = total - i
                if 0 <= j < n:
                    prob += matrix[i, j]
            total_goals_probs[total] = prob

        over_15 = sum(v for k, v in total_goals_probs.items() if k >= 2)
        over_25 = sum(v for k, v in total_goals_probs.items() if k >= 3)
        over_35 = sum(v for k, v in total_goals_probs.items() if k >= 4)

        # Both teams to score
        btts = 0.0
        for i in range(1, n):
            for j in range(1, n):
                btts += matrix[i, j]

        # Clean sheets
        home_cs = sum(matrix[i, 0] for i in range(n))
        away_cs = sum(matrix[0, j] for j in range(n))

        return {
            "over_1_5": round(over_15, 4),
            "over_2_5": round(over_25, 4),
            "over_3_5": round(over_35, 4),
            "btts": round(btts, 4),
            "home_clean_sheet": round(home_cs, 4),
            "away_clean_sheet": round(away_cs, 4),
        }
