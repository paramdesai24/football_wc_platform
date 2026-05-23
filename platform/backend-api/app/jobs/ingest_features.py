from dataclasses import dataclass


@dataclass(frozen=True)
class IngestionJob:
    source_name: str
    target_table: str
    mode: str = "incremental"


def build_default_jobs() -> list[IngestionJob]:
    return [
        IngestionJob(source_name="results.csv", target_table="historical_results"),
        IngestionJob(source_name="players_data-2025_2026.csv", target_table="player_form"),
        IngestionJob(source_name="competitions.csv", target_table="competition_strength"),
    ]
