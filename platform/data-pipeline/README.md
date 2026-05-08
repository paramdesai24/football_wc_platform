# Phase 1: Data Engineering & Football Intelligence Pipeline

Production-grade data engineering architecture for transforming raw football datasets into clean, feature-engineered ML-ready intelligence data.

## Architecture Overview

```
data-pipeline/
├── audit/               # Dataset auditing & quality inspection
├── cleaning/            # Data normalization & cleaning pipelines
├── ingestion/           # Data loading & ingestion utilities
├── feature-engineering/ # Player & country feature engineering
├── exports/             # CSV export & SQLite database integration
├── utils/               # Shared utilities (logging, validation, constants)
├── logs/                # Pipeline execution logs & reports
├── processed-data/      # Output datasets (master files)
├── pipeline.py          # Main orchestration pipeline
└── README.md            # This file
```

## Key Features

### 1. Dataset Auditing System
- **Location**: `audit/auditor.py`
- **Output**: `logs/audit_report.json`
- **Analyzes**:
  - Schema inspection
  - Missing values analysis
  - Duplicate detection
  - Column statistics
  - Issue flagging

### 2. Data Cleaning Pipelines
- **Location**: `cleaning/cleaner.py`
- **Normalizes**:
  - Player names (accents, spacing)
  - Country names (mapping inconsistencies)
  - Club names (suffixes, formatting)
  - Positions (standardization)
  - Market values (currency parsing)
  - Date formats
  - Duplicate records

### 3. Feature Engineering
- **Player Features** (`feature-engineering/player_features.py`):
  - Goals/assists per 90 minutes
  - Consistency scores (goal variance)
  - Recent form scoring (365-day window)
  - Recency-weighted form scores (50% recent, 30% season, 20% historical)
  - Contribution metrics
  
- **Country Features** (`feature-engineering/country_features.py`):
  - Win rate & goal statistics
  - Attack/defense ratings
  - Historical strength scoring
  - Recent form (last 365 days)
  - Squad aggregation
  - Competition strength weighting

### 4. Master Datasets

**master_players.csv**
```
player_id, name, country, club, position, age, market_value,
goals, assists, minutes_played, games_played,
goals_per_90, assists_per_90, contribution_per_90,
form_score, consistency_score
```

**master_countries.csv**
```
country, confederation, total_matches, wins, draws, losses,
win_rate, goals_for, goals_against, goals_per_match,
conceded_per_match, attack_rating, defense_rating,
historical_strength, recent_form_score
```

**squad_aggregates.csv**
```
country, squad_size, total_market_value, avg_player_value,
avg_goals_per_90, avg_assists_per_90, avg_form_score,
avg_consistency_score, squad_strength
```

### 5. SQLite Database Integration
- **Location**: `exports/database.py`
- **Database**: `football_intelligence.db`
- **Tables**: players, countries, squad_aggregates, pipeline_metadata
- **Capabilities**: Insert, query, logging

## Running the Pipeline

### Prerequisites
```bash
cd c:\FIFA WC\platform\backend-api
.\venv\Scripts\Activate.ps1
pip install pandas numpy
```

### Execute Full Pipeline
```bash
cd c:\FIFA WC\platform\data-pipeline
python pipeline.py
```

### Expected Output
```
✓ PHASE 1: DATA ENGINEERING & FOOTBALL INTELLIGENCE PIPELINE
  [STEP 1] Load Datasets                    ✓
  [STEP 2] Dataset Audit                    ✓
  [STEP 3] Data Cleaning                    ✓
  [STEP 4] Feature Engineering              ✓
  [STEP 5] Create Master Datasets           ✓
  [STEP 6] Export Datasets                  ✓
  [STEP 7] Database Integration             ✓
```

## Output Files

### CSV Exports
```
processed-data/
├── master_players.csv        # ~12,000+ rows, unified player database
├── master_countries.csv      # ~200 countries with aggregated metrics
├── player_form.csv           # Per-90 statistics
├── country_strength.csv      # Country intelligence metrics
└── squad_aggregates.csv      # Team/squad composites
```

### Database
```
football_intelligence.db
├── players table             # Master player data
├── countries table           # Master country data
├── squad_aggregates table    # Squad metrics
└── pipeline_metadata table   # Execution logs
```

### Logs
```
logs/
├── pipeline.log              # Detailed execution log
├── audit_report.json         # Dataset quality analysis
├── cleaning_report.json      # Cleaning statistics
├── feature_report.json       # Feature engineering summary
└── pipeline_execution.json   # Full pipeline metadata
```

## Recency Weighting System

**Final Form Score Calculation**:
```
form_score = (
    0.5 * recent_matches (2025-26 season) +
    0.3 * current_season_historical +
    0.2 * historical_average
)
+ 0.1 bonus if in 2025-26 player dataset
```

This ensures recent 2025-26 performance heavily influences predictions while maintaining historical context.

## Data Normalization Examples

### Country Mappings
```
England          → England
South Korea      → South Korea
Korea            → South Korea
Czech Republic   → Czechia
Côte d'Ivoire    → Ivory Coast
Bosnia-Herzegovina → Bosnia and Herzegovina
```

### Position Standardization
```
GK    → Goalkeeper
CB    → Center Back
LB    → Left Back
RB    → Right Back
CM    → Central Midfielder
CAM   → Attacking Midfielder
ST    → Striker
FW    → Forward
```

## Phase 1 Deliverables

✅ Full data pipeline architecture
✅ Comprehensive data auditing system
✅ Reusable cleaning & normalization utilities
✅ Advanced player feature engineering (per-90, form, consistency)
✅ Country-level intelligence aggregation
✅ Squad composition metrics
✅ Recency-weighted form scores (2025-26 bias)
✅ SQLite database integration
✅ CSV export system
✅ Complete logging & error handling
✅ Type hints & documentation
✅ ML-ready dataset outputs

## Next Steps (Phase 2)

- Prediction models (Elo, Poisson, XGBoost)
- Tournament simulation engine
- Real-time API endpoints
- Frontend analytics dashboard
- Player valuation system
- Match outcome predictions

## Architecture Principles

1. **Modular**: Each component is independent and reusable
2. **Maintainable**: Clear separation of concerns
3. **Scalable**: Easy to add new features or datasets
4. **ML-Ready**: Outputs structured for model training
5. **Lightweight**: Pandas + NumPy (no heavy frameworks)
6. **Logged**: Complete audit trail of all operations
7. **Validated**: Data quality checks throughout
8. **Type-Safe**: Type hints where applicable

## Troubleshooting

### Missing Datasets
If datasets are not found, verify:
```
c:\FIFA WC\DATA\
├── intl results/         (results.csv, goalscorers.csv, etc.)
├── transfer market/      (players.csv, games.csv, etc.)
└── latest/              (players_data-2025_2026.csv, etc.)
```

### Database Errors
```bash
# Reset database
rm football_intelligence.db
python pipeline.py
```

### Memory Issues
For large datasets, the pipeline processes in batches. Adjust:
```python
# In utils/constants.py
BATCH_SIZE = 500  # Lower if memory-constrained
```

## Performance Notes

- **Load**: ~5-10 seconds
- **Audit**: ~2-5 seconds
- **Clean**: ~10-20 seconds
- **Engineer Features**: ~15-30 seconds
- **Create Masters**: ~5-10 seconds
- **Export**: ~5 seconds
- **Database**: ~5 seconds

**Total Runtime**: ~60-90 seconds for full pipeline

---

**Last Updated**: May 7, 2026
**Phase**: 1 - Data Engineering & Football Intelligence
**Status**: Production Ready ✓
