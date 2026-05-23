"""Play As A Team mode aggregation helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List


class PlayAsTeamMode:
    """Aggregate selected-team journeys across multiple tournament simulations."""

    FINISH_SCORES = {
        "Champion": 8,
        "Runner-up": 7,
        "Third Place": 6,
        "Fourth Place": 5,
        "Semi-Final": 5,
        "Quarter-Final": 4,
        "Round of 16": 3,
        "Round of 32": 2,
        "Group Stage": 1,
        "Not started": 0,
        "Unknown": 0,
    }

    SCORE_TO_LABEL = {
        8: "Champion",
        7: "Runner-up",
        6: "Third Place",
        5: "Semi-Final",
        4: "Quarter-Final",
        3: "Round of 16",
        2: "Round of 32",
        1: "Group Stage",
        0: "Group Stage",
    }

    def summarize(self, team_name: str, journeys: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not journeys:
            return {
                "team": team_name,
                "simulations": 0,
                "titles_won": 0,
                "average_finish": "N/A",
                "goals_scored": 0,
                "goals_conceded": 0,
                "average_goals_scored": 0.0,
                "average_goals_conceded": 0.0,
                "average_goals_for": 0.0,
                "average_goals_against": 0.0,
                "clean_sheets": 0,
                "et_frequency": 0.0,
                "penalty_frequency": 0.0,
                "elimination_distribution": {},
                "win_probability": 0.0,
            }

        titles = 0
        total_goals_for = 0
        total_goals_against = 0
        total_clean_sheets = 0
        finish_score_sum = 0
        elimination = Counter()
        total_matches = 0
        et_matches = 0
        pen_matches = 0

        for journey in journeys:
            stage_reached = str(journey.get("stage_reached", "Unknown"))
            elimination[stage_reached] += 1
            finish_score_sum += self.FINISH_SCORES.get(stage_reached, 0)
            if stage_reached == "Champion":
                titles += 1

            total_goals_for += int(journey.get("goals_for", 0) or 0)
            total_goals_against += int(journey.get("goals_against", 0) or 0)
            total_clean_sheets += int(journey.get("clean_sheets", 0) or 0)

            for match in journey.get("matches", []):
                total_matches += 1
                if bool(match.get("extra_time", False)):
                    et_matches += 1
                if bool(match.get("penalties", False)):
                    pen_matches += 1

        simulations = len(journeys)
        avg_finish_score = round(finish_score_sum / simulations)
        average_finish = self.SCORE_TO_LABEL.get(avg_finish_score, "Group Stage")

        return {
            "team": team_name,
            "simulations": simulations,
            "titles_won": titles,
            "average_finish": average_finish,
            "goals_scored": total_goals_for,
            "goals_conceded": total_goals_against,
            "average_goals_scored": round(total_goals_for / simulations, 2),
            "average_goals_conceded": round(total_goals_against / simulations, 2),
            "average_goals_for": round(total_goals_for / simulations, 2),
            "average_goals_against": round(total_goals_against / simulations, 2),
            "clean_sheets": total_clean_sheets,
            "et_frequency": round(et_matches / total_matches, 3) if total_matches else 0.0,
            "penalty_frequency": round(pen_matches / total_matches, 3) if total_matches else 0.0,
            "elimination_distribution": dict(elimination),
            "win_probability": round(titles / simulations, 3),
        }
