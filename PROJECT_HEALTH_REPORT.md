# Project Health Report — Football Intelligence Pipeline

## Architecture
- Monorepo with `platform/data-pipeline` as canonical pipeline root.
- Centralized processed outputs located at `platform/data/processed`.
- SQLite database `football_intelligence.db` stored at `platform/data/processed`.

## Completed Systems
- Schema registry, entity registry, fuzzy matching, and entity resolution.
- Feature engineering: recent-form, per-90 metrics, consistency scoring.
- Aggregation: master players/countries, squad aggregates, feature lineage.
- Exports: CSV exports and SQLite integration via `exports/database.py`.
- Validation: `utils/generate_validation_reports.py` and `run_validation.py`.

## Current Readiness
- Pipeline runs end-to-end using module execution (`python -m run_validation` etc.).
- Centralized artifacts present in `platform/data/processed` and logs in `platform/data-pipeline/logs`.

## Remaining Technical Debt
- `club_uid` appears to be missing or not populated (all entries duplicated); requires investigation in aggregation UID generation.
- `master_countries` contains multiple rows mapping to the same normalized country (duplicates after normalization: 275). Consider consolidating by `country_uid`.
- Some scripts still reference legacy paths — codebase scans recommended before release.

## Next Steps
1. Fix `club_uid` generation in `run_aggregation.py`/entity resolution.
2. Consolidate `master_countries` by canonical `country_uid` and re-run exports.
3. Add CI checks to run `python -m run_validation` and fail on regressions.

Generated on: 2026-05-08
