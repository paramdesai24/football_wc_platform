"""
Prediction Exporter
====================
Exports match predictions, expected goals, scoreline probabilities,
and explainability data to CSV files and SQLite database.
"""

import logging
import json
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from ..utils.constants import EXPORTS_DIR, DB_PATH, LOGS_DIR

logger = logging.getLogger("match_engine.exporter")


class PredictionExporter:
    """Export predictions to CSV and SQLite."""

    def __init__(self, output_dir: Path = EXPORTS_DIR):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

    def export_predictions_csv(self, predictions: List[Dict[str, Any]]) -> Path:
        """Export match predictions to CSV."""
        rows = []
        for p in predictions:
            rows.append({
                "home_team": p.get("home_team"),
                "away_team": p.get("away_team"),
                "predicted_winner": p.get("predicted_winner"),
                "home_win_prob": p.get("home_win_prob"),
                "draw_prob": p.get("draw_prob"),
                "away_win_prob": p.get("away_win_prob"),
                "home_xg": p.get("home_xg"),
                "away_xg": p.get("away_xg"),
                "predicted_score": p.get("predicted_score"),
                "score_probability": p.get("score_probability"),
                "confidence_score": p.get("confidence_score", ""),
                "confidence_tier": p.get("confidence_tier", ""),
                "explanation": p.get("explanation", ""),
                "venue": p.get("venue", "neutral"),
                "tournament": p.get("tournament", "friendly"),
            })
        df = pd.DataFrame(rows)
        path = self.output_dir / "match_predictions.csv"
        df.to_csv(path, index=False)
        logger.info("Exported %d predictions to %s", len(df), path)
        return path

    def export_expected_goals_csv(self, predictions: List[Dict]) -> Path:
        """Export expected goals data to CSV."""
        rows = []
        for p in predictions:
            rows.append({
                "home_team": p.get("home_team"),
                "away_team": p.get("away_team"),
                "home_xg": p.get("home_xg"),
                "away_xg": p.get("away_xg"),
                "total_xg": p.get("total_xg"),
                "predicted_home_goals": p.get("predicted_home_goals"),
                "predicted_away_goals": p.get("predicted_away_goals"),
            })
        df = pd.DataFrame(rows)
        path = self.output_dir / "expected_goals.csv"
        df.to_csv(path, index=False)
        logger.info("Exported expected goals to %s", path)
        return path

    def export_scoreline_probs_csv(self, predictions: List[Dict]) -> Path:
        """Export top scoreline probabilities to CSV."""
        rows = []
        for p in predictions:
            home = p.get("home_team", "")
            away = p.get("away_team", "")
            for s in p.get("top_scorelines", []):
                rows.append({
                    "home_team": home,
                    "away_team": away,
                    "scoreline": s.get("scoreline"),
                    "home_goals": s.get("home_goals"),
                    "away_goals": s.get("away_goals"),
                    "probability": s.get("probability"),
                })
        df = pd.DataFrame(rows)
        path = self.output_dir / "scoreline_probabilities.csv"
        df.to_csv(path, index=False)
        logger.info("Exported scoreline probabilities to %s", path)
        return path

    def export_explainability_csv(self, explanations: List[Dict]) -> Path:
        """Export prediction explainability data."""
        rows = []
        for e in explanations:
            row = {
                "home_team": e.get("home_team"),
                "away_team": e.get("away_team"),
                "narrative": e.get("narrative"),
                "confidence_note": e.get("confidence_note"),
            }
            for factor in e.get("factor_summary", []):
                key = factor["factor"].lower().replace(" ", "_")
                row[f"{key}_weight"] = factor["weight"]
                row[f"{key}_favors"] = factor["favors"]

            advantages = e.get("advantages", {})
            for cat, adv in advantages.items():
                row[f"{cat}_advantage"] = adv["advantage"]
                row[f"{cat}_diff"] = adv["difference"]

            key_factors = e.get("key_factors", [])
            row["key_factors"] = " | ".join(key_factors)

            rows.append(row)

        df = pd.DataFrame(rows)
        path = self.output_dir / "prediction_explainability.csv"
        df.to_csv(path, index=False)
        logger.info("Exported explainability to %s", path)
        return path

    def export_to_sqlite(self, predictions: List[Dict]) -> Path:
        """Export predictions to SQLite database."""
        db_path = DB_PATH
        conn = sqlite3.connect(str(db_path))
        try:
            # Match predictions table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS match_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    home_team TEXT,
                    away_team TEXT,
                    predicted_winner TEXT,
                    home_win_prob REAL,
                    draw_prob REAL,
                    away_win_prob REAL,
                    home_xg REAL,
                    away_xg REAL,
                    predicted_score TEXT,
                    confidence_score REAL,
                    confidence_tier TEXT,
                    venue TEXT,
                    tournament TEXT,
                    explanation TEXT,
                    created_at TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS expected_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    home_team TEXT,
                    away_team TEXT,
                    home_xg REAL,
                    away_xg REAL,
                    total_xg REAL,
                    created_at TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS prediction_confidence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    home_team TEXT,
                    away_team TEXT,
                    confidence_score REAL,
                    confidence_tier TEXT,
                    created_at TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS scoreline_probabilities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    home_team TEXT,
                    away_team TEXT,
                    scoreline TEXT,
                    probability REAL,
                    created_at TEXT
                )
            """)

            now = datetime.now().isoformat()

            for p in predictions:
                conn.execute(
                    """INSERT INTO match_predictions
                    (home_team, away_team, predicted_winner, home_win_prob,
                     draw_prob, away_win_prob, home_xg, away_xg, predicted_score,
                     confidence_score, confidence_tier, venue, tournament,
                     explanation, created_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (p.get("home_team"), p.get("away_team"),
                     p.get("predicted_winner"), p.get("home_win_prob"),
                     p.get("draw_prob"), p.get("away_win_prob"),
                     p.get("home_xg"), p.get("away_xg"),
                     p.get("predicted_score"), p.get("confidence_score"),
                     p.get("confidence_tier"), p.get("venue"),
                     p.get("tournament"), p.get("explanation"), now),
                )

                conn.execute(
                    """INSERT INTO expected_goals
                    (home_team, away_team, home_xg, away_xg, total_xg, created_at)
                    VALUES (?,?,?,?,?,?)""",
                    (p.get("home_team"), p.get("away_team"),
                     p.get("home_xg"), p.get("away_xg"),
                     p.get("total_xg"), now),
                )

                conn.execute(
                    """INSERT INTO prediction_confidence
                    (home_team, away_team, confidence_score, confidence_tier, created_at)
                    VALUES (?,?,?,?,?)""",
                    (p.get("home_team"), p.get("away_team"),
                     p.get("confidence_score"), p.get("confidence_tier"), now),
                )

                for s in p.get("top_scorelines", []):
                    conn.execute(
                        """INSERT INTO scoreline_probabilities
                        (home_team, away_team, scoreline, probability, created_at)
                        VALUES (?,?,?,?,?)""",
                        (p.get("home_team"), p.get("away_team"),
                         s.get("scoreline"), s.get("probability"), now),
                    )

            conn.commit()
            logger.info("Exported %d predictions to SQLite: %s", len(predictions), db_path)
        finally:
            conn.close()

        return db_path

    def export_validation_json(self, predictions: List[Dict]) -> Path:
        """Generate and export validation report."""
        issues = []
        for p in predictions:
            h = p.get("home_win_prob", 0)
            d = p.get("draw_prob", 0)
            a = p.get("away_win_prob", 0)
            total = h + d + a

            if abs(total - 1.0) > 0.01:
                issues.append({
                    "match": f"{p.get('home_team')} vs {p.get('away_team')}",
                    "issue": "probabilities_dont_sum_to_1",
                    "total": round(total, 4),
                })

            if p.get("home_xg", 0) > 5.0 or p.get("away_xg", 0) > 5.0:
                issues.append({
                    "match": f"{p.get('home_team')} vs {p.get('away_team')}",
                    "issue": "unrealistic_xg",
                    "home_xg": p.get("home_xg"),
                    "away_xg": p.get("away_xg"),
                })

            if h < 0 or d < 0 or a < 0:
                issues.append({
                    "match": f"{p.get('home_team')} vs {p.get('away_team')}",
                    "issue": "negative_probability",
                })

        report = {
            "timestamp": datetime.now().isoformat(),
            "total_predictions": len(predictions),
            "validation_passed": len(issues) == 0,
            "issues_count": len(issues),
            "issues": issues,
            "checks": {
                "probability_sum": "PASS" if not any(i["issue"] == "probabilities_dont_sum_to_1" for i in issues) else "FAIL",
                "realistic_xg": "PASS" if not any(i["issue"] == "unrealistic_xg" for i in issues) else "FAIL",
                "non_negative": "PASS" if not any(i["issue"] == "negative_probability" for i in issues) else "FAIL",
            },
        }

        path = self.output_dir / "prediction_validation.json"
        with open(path, "w") as f:
            json.dump(report, f, indent=2)
        logger.info("Validation report: %s (issues: %d)", path, len(issues))
        return path
