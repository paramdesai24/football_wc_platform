"""
Realism Constraints Engine
===========================
Applies football realism constraints to prevent unrealistic probabilities
and scoreline distributions that don't match observed international football data.

Constraints:
1. Max upset probability: Weaker teams can't have >50% chance vs elite
2. Max goals against elite teams: Elite defenses suppress goals
3. Defensive suppression: Strong teams concede fewer goals
4. Low probability of 5+ goal wins: Blowouts are rare in modern football
5. Draw probability floor: Even elite teams draw occasionally
"""

import logging
from typing import Dict, Any
import numpy as np

logger = logging.getLogger("match_engine.realism")


class RealismConstraintsEngine:
    """
    Applies football realism constraints to match predictions
    to ensure realistic bounds on probabilities and outcomes.
    """

    # Elite team thresholds (Elo or rating-based)
    ELITE_ELO_THRESHOLD = 1800
    ELITE_OFFENSE_RATING = 85.0
    ELITE_DEFENSE_RATING = 85.0

    # Realistic probability caps
    MAX_UPSET_VS_ELITE = 0.35        # Weaker team beats elite with max 35% probability
    MAX_BLOWOUT_WIN_PROB = 0.15      # Probability of 5+ goal wins capped at 15%
    MIN_DRAW_PROBABILITY = 0.08      # Even huge mismatches have minimum 8% draw chance

    def __init__(self):
        pass

    def apply_constraints(
        self,
        prediction: Dict[str, Any],
        home_data: Dict[str, Any],
        away_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Apply realism constraints to a match prediction.
        
        Modifies:
        - home_win_prob, draw_prob, away_win_prob (sum to 1.0)
        - xG values (capped based on opponent strength)
        - Market probabilities
        
        Returns modified prediction dict
        """
        constrained = prediction.copy()

        # 1. Apply upset probability caps
        constrained = self._constrain_upsets(constrained, home_data, away_data)

        # 2. Apply elite team defensive suppression
        constrained = self._constrain_elite_defense(constrained, home_data, away_data)

        # 3. Apply blowout probability cap
        constrained = self._constrain_blowouts(constrained)

        # 4. Ensure minimum draw probability
        constrained = self._constrain_draw_floor(constrained)

        return constrained

    def _constrain_upsets(
        self,
        prediction: Dict[str, Any],
        home_data: Dict[str, Any],
        away_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Cap upset probabilities: weaker teams can't have too high a win chance vs elite.
        
        Elite defined by: Elo >= 1800 OR (offensive_rating >= 85 AND defensive_rating >= 85)
        """
        home_elo = home_data.get("elo_rating", 1500)
        away_elo = away_data.get("elo_rating", 1500)
        
        home_off = home_data.get("offensive_rating", 75)
        home_def = home_data.get("defensive_rating", 83)
        away_off = away_data.get("offensive_rating", 75)
        away_def = away_data.get("defensive_rating", 83)

        home_elite = (home_elo >= self.ELITE_ELO_THRESHOLD) or (
            home_off >= self.ELITE_OFFENSE_RATING and home_def >= self.ELITE_DEFENSE_RATING
        )
        away_elite = (away_elo >= self.ELITE_ELO_THRESHOLD) or (
            away_off >= self.ELITE_OFFENSE_RATING and away_def >= self.ELITE_DEFENSE_RATING
        )

        h_win = prediction.get("home_win_prob", 0.33)
        d_prob = prediction.get("draw_prob", 0.28)
        a_win = prediction.get("away_win_prob", 0.39)

        # If home is elite and away isn't, cap away's win probability
        if home_elite and not away_elite:
            a_win = min(a_win, self.MAX_UPSET_VS_ELITE)
        
        # If away is elite and home isn't, cap home's win probability
        if away_elite and not home_elite:
            h_win = min(h_win, self.MAX_UPSET_VS_ELITE)

        # Re-normalize probabilities to sum to 1.0
        total = h_win + d_prob + a_win
        if total > 0:
            h_win /= total
            d_prob /= total
            a_win /= total

        prediction["home_win_prob"] = round(h_win, 4)
        prediction["draw_prob"] = round(d_prob, 4)
        prediction["away_win_prob"] = round(a_win, 4)

        return prediction

    def _constrain_elite_defense(
        self,
        prediction: Dict[str, Any],
        home_data: Dict[str, Any],
        away_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Elite teams with strong defense concede fewer goals.
        Reduce xG against elite defenses by 10-15%.
        """
        home_def = home_data.get("defensive_rating", 83)
        away_def = away_data.get("defensive_rating", 83)

        away_xg = prediction.get("away_xg", 1.35)
        home_xg = prediction.get("home_xg", 1.35)

        # If home defense is elite (>87), reduce away's xG
        if home_def > 87:
            reduction = min(0.15, (home_def - 87) / 100)  # Max 15% reduction
            away_xg = max(0.4, away_xg * (1 - reduction))

        # If away defense is elite (>87), reduce home's xG
        if away_def > 87:
            reduction = min(0.15, (away_def - 87) / 100)  # Max 15% reduction
            home_xg = max(0.4, home_xg * (1 - reduction))

        prediction["home_xg"] = round(home_xg, 2)
        prediction["away_xg"] = round(away_xg, 2)
        prediction["total_xg"] = round(home_xg + away_xg, 2)

        return prediction

    def _constrain_blowouts(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cap the probability of 5+ goal wins (blowouts) at 15%.
        Adjust market probabilities accordingly.
        """
        markets = prediction.get("markets", {})
        
        # Cap 5+ goals probability
        if "5_plus_goals" in markets:
            markets["5_plus_goals"] = min(0.15, markets["5_plus_goals"])
        
        if "over_2_5_goals" in markets:
            # Over 2.5 is more common, but cap extreme values
            markets["over_2_5_goals"] = min(0.65, markets["over_2_5_goals"])
        
        prediction["markets"] = markets
        return prediction

    def _constrain_draw_floor(self, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure minimum draw probability of 8%.
        Even huge mismatches occasionally have draws.
        """
        d_prob = prediction.get("draw_prob", 0.28)
        
        if d_prob < self.MIN_DRAW_PROBABILITY:
            # Adjust all probabilities, keeping ratio of home/away wins
            h_win = prediction.get("home_win_prob", 0.33)
            a_win = prediction.get("away_win_prob", 0.39)
            
            adjustment = self.MIN_DRAW_PROBABILITY - d_prob
            total_adjust = h_win + a_win
            
            if total_adjust > 0:
                h_win = max(0.01, h_win - adjustment * (h_win / total_adjust))
                a_win = max(0.01, a_win - adjustment * (a_win / total_adjust))
                d_prob = self.MIN_DRAW_PROBABILITY
                
                # Final normalization
                total = h_win + d_prob + a_win
                h_win /= total
                d_prob /= total
                a_win /= total

            prediction["home_win_prob"] = round(h_win, 4)
            prediction["draw_prob"] = round(d_prob, 4)
            prediction["away_win_prob"] = round(a_win, 4)

        return prediction
