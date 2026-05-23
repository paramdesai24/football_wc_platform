"""
FIFA World Cup 2026 — Tournament Export Engine
================================================
Exports all tournament data to CSV, JSON, and SQLite.
"""
import sys
import json
import csv
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tournament_engine.utils.logging_config import setup_logging
from tournament_engine.utils.constants import EXPORTS_DIR, DB_PATH
from tournament_engine.simulation.tournament import TournamentSimulator

logger = setup_logging("tournament.exports")


def export_to_sqlite(sim: TournamentSimulator):
    """Export tournament data to SQLite database."""
    db_path = DB_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tournament_matches (
            match_id TEXT PRIMARY KEY,
            stage TEXT,
            group_name TEXT,
            matchday INTEGER,
            home_team TEXT,
            away_team TEXT,
            home_goals INTEGER,
            away_goals INTEGER,
            home_xg REAL,
            away_xg REAL,
            winner TEXT,
            loser TEXT,
            extra_time INTEGER DEFAULT 0,
            penalties INTEGER DEFAULT 0,
            penalty_score TEXT,
            result_type TEXT,
            home_win_prob REAL,
            away_win_prob REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_standings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            position INTEGER,
            team TEXT,
            played INTEGER,
            won INTEGER,
            drawn INTEGER,
            lost INTEGER,
            goals_for INTEGER,
            goals_against INTEGER,
            goal_difference INTEGER,
            points INTEGER
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tournament_probabilities (
            team TEXT PRIMARY KEY,
            group_advance_prob REAL,
            group_exit_prob REAL,
            r32_prob REAL,
            r16_prob REAL,
            qf_prob REAL,
            sf_prob REAL,
            final_prob REAL,
            champion_prob REAL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tournament_bracket (
            match_id TEXT PRIMARY KEY,
            stage TEXT,
            home_team TEXT,
            away_team TEXT,
            home_goals INTEGER,
            away_goals INTEGER,
            winner TEXT,
            extra_time INTEGER DEFAULT 0,
            penalties INTEGER DEFAULT 0,
            penalty_score TEXT,
            home_from TEXT,
            away_from TEXT
        )
    """)

    # Clear existing data
    cursor.execute("DELETE FROM tournament_matches")
    cursor.execute("DELETE FROM group_standings")
    cursor.execute("DELETE FROM tournament_bracket")

    state = sim.get_tournament_state()

    # Insert group results
    for r in state.get("group_results", []):
        cursor.execute("""
            INSERT INTO tournament_matches
            (match_id, stage, group_name, matchday, home_team, away_team,
             home_goals, away_goals, home_xg, away_xg, winner, loser,
             home_win_prob, away_win_prob, result_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            r.get("match_id", ""),
            "group",
            r.get("group", ""),
            r.get("matchday", 0),
            r.get("home_team", ""),
            r.get("away_team", ""),
            r.get("home_goals", 0),
            r.get("away_goals", 0),
            r.get("home_xg", 0),
            r.get("away_xg", 0),
            r.get("home_team") if r.get("result") == "home_win" else
            r.get("away_team") if r.get("result") == "away_win" else None,
            r.get("away_team") if r.get("result") == "home_win" else
            r.get("home_team") if r.get("result") == "away_win" else None,
            r.get("home_win_prob", 0),
            r.get("away_win_prob", 0),
            r.get("result", ""),
        ))

    # Insert knockout results
    for r in state.get("knockout_results", []):
        cursor.execute("""
            INSERT INTO tournament_matches
            (match_id, stage, home_team, away_team, home_goals, away_goals,
             home_xg, away_xg, winner, loser, extra_time, penalties,
             penalty_score, result_type, home_win_prob, away_win_prob)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(r.get("match_id", "")),
            r.get("stage", ""),
            r.get("home_team", ""),
            r.get("away_team", ""),
            r.get("home_goals", 0),
            r.get("away_goals", 0),
            r.get("home_xg", 0),
            r.get("away_xg", 0),
            r.get("winner", ""),
            r.get("loser", ""),
            1 if r.get("extra_time") else 0,
            1 if r.get("penalties") else 0,
            r.get("penalty_score"),
            r.get("result_type", ""),
            r.get("home_win_prob", 0),
            r.get("away_win_prob", 0),
        ))

    # Insert standings
    for group, standings in state.get("group_standings", {}).items():
        for s in standings:
            cursor.execute("""
                INSERT INTO group_standings
                (group_name, position, team, played, won, drawn, lost,
                 goals_for, goals_against, goal_difference, points)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                group,
                s.get("position", 0),
                s.get("team", ""),
                s.get("played", 0),
                s.get("won", 0),
                s.get("drawn", 0),
                s.get("lost", 0),
                s.get("goals_for", 0),
                s.get("goals_against", 0),
                s.get("goal_difference", 0),
                s.get("points", 0),
            ))

    # Insert bracket tree
    bracket = state.get("bracket", {})
    for stage_key in ["r32", "r16", "qf", "sf"]:
        for m in bracket.get(stage_key, []):
            cursor.execute("""
                INSERT OR REPLACE INTO tournament_bracket
                (match_id, stage, home_team, away_team, home_goals,
                 away_goals, winner, extra_time, penalties, penalty_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(m.get("match_id", "")),
                stage_key.upper(),
                m.get("home_team", ""),
                m.get("away_team", ""),
                m.get("home_goals"),
                m.get("away_goals"),
                m.get("winner"),
                1 if m.get("extra_time") else 0,
                1 if m.get("penalties") else 0,
                m.get("penalty_score"),
            ))

    for key in ["third_place", "final"]:
        m = bracket.get(key, {})
        if m:
            cursor.execute("""
                INSERT OR REPLACE INTO tournament_bracket
                (match_id, stage, home_team, away_team, home_goals,
                 away_goals, winner, extra_time, penalties, penalty_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(m.get("match_id", "")),
                key.upper(),
                m.get("home_team", ""),
                m.get("away_team", ""),
                m.get("home_goals"),
                m.get("away_goals"),
                m.get("winner"),
                1 if m.get("extra_time") else 0,
                1 if m.get("penalties") else 0,
                m.get("penalty_score"),
            ))

    conn.commit()
    conn.close()
    logger.info("Tournament data exported to SQLite: %s", db_path)


def export_bracket_csv(sim: TournamentSimulator):
    """Export bracket to CSV."""
    path = EXPORTS_DIR / "knockout_bracket.csv"
    bracket = sim._bracket.get_bracket_tree()

    fields = ["match_id", "stage", "home_team", "away_team",
              "home_goals", "away_goals", "winner", "extra_time",
              "penalties", "penalty_score"]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for stage in ["r32", "r16", "qf", "sf"]:
            for m in bracket.get(stage, []):
                writer.writerow(m)
        for key in ["third_place", "final"]:
            m = bracket.get(key)
            if m:
                writer.writerow(m)
    logger.info("Bracket exported to %s", path)


def export_tournament_tree(sim: TournamentSimulator):
    """Export full bracket tree as JSON."""
    path = EXPORTS_DIR / "tournament_tree.json"
    tree = sim._bracket.get_bracket_tree()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(tree, f, indent=2, ensure_ascii=False)
    logger.info("Tournament tree exported to %s", path)


def main():
    print("\n" + "=" * 70)
    print("  FIFA WORLD CUP 2026 — TOURNAMENT EXPORTS")
    print("=" * 70)

    seed = 2026
    if len(sys.argv) > 1:
        try:
            seed = int(sys.argv[1])
        except ValueError:
            pass

    sim = TournamentSimulator(seed=seed, stochastic=True)
    sim.run()

    # CSV exports
    sim.export_group_csv()
    sim.export_knockout_csv()
    export_bracket_csv(sim)
    export_tournament_tree(sim)
    sim.save_state()

    # SQLite export
    export_to_sqlite(sim)

    # MC probabilities (quick 50-run)
    print("\n  Running 50-simulation MC for probabilities...")
    from tournament_engine.simulation.monte_carlo import MonteCarloTournament
    mc = MonteCarloTournament(n_simulations=50, base_seed=seed)
    mc.run()
    mc.export_probabilities()
    mc.export_summary()

    # Import probabilities into SQLite
    probs_path = EXPORTS_DIR / "tournament_probabilities.csv"
    if probs_path.exists():
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tournament_probabilities")
        with open(probs_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cursor.execute("""
                    INSERT OR REPLACE INTO tournament_probabilities
                    (team, group_advance_prob, group_exit_prob, r32_prob,
                     r16_prob, qf_prob, sf_prob, final_prob, champion_prob)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row["team"],
                    float(row.get("group_advance_prob", 0)),
                    float(row.get("group_exit_prob", 0)),
                    float(row.get("r32_prob", 0)),
                    float(row.get("r16_prob", 0)),
                    float(row.get("qf_prob", 0)),
                    float(row.get("sf_prob", 0)),
                    float(row.get("final_prob", 0)),
                    float(row.get("champion_prob", 0)),
                ))
        conn.commit()
        conn.close()
        logger.info("Probabilities imported to SQLite")

    print(f"\n{'=' * 70}")
    print(f"  All exports complete!")
    print(f"  CSV:    {EXPORTS_DIR}")
    print(f"  SQLite: {DB_PATH}")
    print(f"  Champion: {sim.champion}")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
