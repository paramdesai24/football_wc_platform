# Phase 1 to Backend Integration

**Status**: Foundation Complete ✅  
**Ready for**: Phase 2 API Endpoints

---

## INTEGRATION OVERVIEW

The Phase 1 data pipeline outputs are consumed by the FastAPI backend in three ways:

### 1. **CSV Files** (Direct Analysis)
- Location: `/platform/data-pipeline/processed-data/`
- Use: Data science exploratory work, external tools
- Format: CSV (human-readable, tool-compatible)

### 2. **SQLite Database** (Production API Access)
- Location: `/platform/backend-api/data/football_intelligence.db`
- Use: FastAPI endpoints to query processed intelligence data
- Format: SQL (CRUD operations, efficient)

### 3. **Pipeline Logs** (Data Quality)
- Location: `/platform/data-pipeline/logs/`
- Use: Audit trail, debugging, data quality reports
- Format: JSON (machine-readable, indexable)

---

## CURRENT STATE

### Phase 1 Deliverables ✅
- ✅ Data audit system
- ✅ Cleaning pipelines
- ✅ Feature engineering (player + country)
- ✅ Master dataset creation
- ✅ SQLite integration
- ✅ CSV export
- ✅ Complete logging

### Phase 2 Tasks (Not Yet Started)
- ❌ API endpoints to query pipeline data
- ❌ Elo rating system
- ❌ Poisson model
- ❌ XGBoost predictions
- ❌ Tournament simulator
- ❌ Real-time auction service

---

## HOW PHASE 2 WILL CONSUME THIS DATA

### Scenario 1: Prediction Model Training (XGBoost)

```python
# Phase 2 Prediction Service
from platform.data_pipeline.exports.database import FootballIntelligenceDB
import pandas as pd

# Load processed players
db = FootballIntelligenceDB()
master_players = db.get_players()

# Extract features for model
X = master_players[[
    'goals_per_90', 'assists_per_90', 'form_score', 
    'consistency_score', 'market_value', 'age'
]]
y = master_players['goals']  # Target: actual goals

# Train model
model.fit(X, y)
```

### Scenario 2: Tournament Simulation

```python
# Phase 2 Simulation Engine
db = FootballIntelligenceDB()

# Get squad strength scores
teams = db.query("SELECT country, squad_strength FROM squad_aggregates")

# Simulate match
for match in upcoming_matches:
    team_a_strength = teams[teams['country'] == match.team_a]['squad_strength']
    team_b_strength = teams[teams['country'] == match.team_b]['squad_strength']
    
    # Use form_score + strength to predict outcome
    probabilities = predict_match_outcome(team_a_strength, team_b_strength)
```

### Scenario 3: Player Analytics Dashboard

```python
# Phase 2 Frontend API Endpoint
from fastapi import APIRouter

router = APIRouter()

@router.get("/api/v1/players/{country}")
def get_country_squad(country: str):
    db = FootballIntelligenceDB()
    
    # Query phase 1 processed data
    squad = db.query(f"""
        SELECT name, position, goals_per_90, assists_per_90, 
               form_score, market_value 
        FROM players 
        WHERE country = '{country}'
        ORDER BY form_score DESC
    """)
    
    return squad.to_dict('records')
```

---

## DATA FLOW ARCHITECTURE

```
RAW DATA (DATA/)
    ↓
    ├─ intl results/
    ├─ transfer market/
    └─ latest/
    
        ↓
        
PHASE 1: DATA PIPELINE (data-pipeline/)
    ├─ Load Datasets
    ├─ Audit (logs/audit_report.json)
    ├─ Clean (cleaning/cleaner.py)
    ├─ Engineer Features (feature-engineering/)
    ├─ Create Masters
    ├─ Export CSV (processed-data/)
    └─ Store SQLite (football_intelligence.db)
    
        ↓
        
PROCESSED DATA OUTPUTS
    ├─ CSV Files (processed-data/)
    ├─ SQLite Database (football_intelligence.db)
    └─ Pipeline Logs (logs/)
    
        ↓
        
PHASE 2: ML & BACKEND (backend-api/ + frontend/)
    ├─ Prediction Models (Elo, Poisson, XGBoost)
    ├─ Tournament Simulator
    ├─ API Endpoints
    └─ Analytics Dashboard
```

---

## EXECUTING THE PIPELINE

### Step 1: Activate Environment
```bash
cd c:\FIFA WC\platform\backend-api
.\venv\Scripts\Activate.ps1
```

### Step 2: Run Pipeline
```bash
cd ..\data-pipeline
python pipeline.py
```

### Step 3: Verify Output
```bash
# Check CSV files
ls processed-data/
# Output:
# master_players.csv
# master_countries.csv
# squad_aggregates.csv
# ...

# Check database
python -c "import sqlite3; conn = sqlite3.connect('..\backend-api\data\football_intelligence.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM players'); print(f'Players: {cursor.fetchone()[0]}')"
```

---

## DATABASE SCHEMA

### Players Table
```sql
CREATE TABLE players (
    player_id TEXT PRIMARY KEY,
    name TEXT,
    country TEXT,
    club TEXT,
    position TEXT,
    age INTEGER,
    market_value REAL,
    goals INTEGER,
    assists INTEGER,
    minutes_played INTEGER,
    games_played INTEGER,
    goals_per_90 REAL,
    assists_per_90 REAL,
    contribution_per_90 REAL,
    form_score REAL,  -- 0-1, weighted by 2025-26 recency
    consistency_score REAL,  -- 0-1
    created_at TIMESTAMP
);
```

### Countries Table
```sql
CREATE TABLE countries (
    country TEXT PRIMARY KEY,
    confederation TEXT,
    total_matches INTEGER,
    wins INTEGER,
    draws INTEGER,
    losses INTEGER,
    win_rate REAL,
    goals_for INTEGER,
    goals_against INTEGER,
    goals_per_match REAL,
    conceded_per_match REAL,
    attack_rating REAL,  -- 0-100
    defense_rating REAL,  -- 0-100
    historical_strength REAL,  -- 0-1
    recent_form_score REAL,  -- 0-1
    created_at TIMESTAMP
);
```

### Squad Aggregates Table
```sql
CREATE TABLE squad_aggregates (
    country TEXT PRIMARY KEY,
    squad_size INTEGER,
    total_market_value REAL,
    avg_player_value REAL,
    avg_goals_per_90 REAL,
    avg_assists_per_90 REAL,
    avg_form_score REAL,
    avg_consistency_score REAL,
    squad_strength REAL,  -- Composite score 0-1
    created_at TIMESTAMP
);
```

---

## QUERYING THE DATABASE FROM FASTAPI

### Setup Repository
```python
# app/repositories/intelligence_repository.py

from app.core.database import get_session
from sqlalchemy import text

class IntelligenceRepository:
    @staticmethod
    def get_players_by_country(session, country: str):
        """Get all players from a country."""
        result = session.execute(
            text("""
                SELECT * FROM players 
                WHERE country = :country 
                ORDER BY form_score DESC
            """),
            {"country": country}
        )
        return result.fetchall()
    
    @staticmethod
    def get_top_scorers(session, limit: int = 10):
        """Get top scorers by goals_per_90."""
        result = session.execute(
            text("""
                SELECT name, country, position, goals_per_90, form_score
                FROM players 
                ORDER BY goals_per_90 DESC 
                LIMIT :limit
            """),
            {"limit": limit}
        )
        return result.fetchall()
    
    @staticmethod
    def get_country_strength(session, country: str):
        """Get country intelligence."""
        result = session.execute(
            text("""
                SELECT * FROM countries 
                WHERE country = :country
            """),
            {"country": country}
        )
        return result.fetchone()
```

### Create Endpoint
```python
# app/api/v1/intelligence.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.intelligence_repository import IntelligenceRepository

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

@router.get("/players/{country}")
def get_country_squad(country: str, db: Session = Depends(get_db)):
    """Get squad players with form scores."""
    players = IntelligenceRepository.get_players_by_country(db, country)
    return players

@router.get("/top-scorers")
def get_top_scorers(limit: int = 10, db: Session = Depends(get_db)):
    """Get top scorers by goals per 90."""
    scorers = IntelligenceRepository.get_top_scorers(db, limit)
    return scorers

@router.get("/country/{country}/strength")
def get_country_intelligence(country: str, db: Session = Depends(get_db)):
    """Get country-level intelligence."""
    intelligence = IntelligenceRepository.get_country_strength(db, country)
    return intelligence
```

---

## PIPELINE EXECUTION SCHEDULE

### Development (Ad-hoc)
```bash
# Run when new data available
python pipeline.py
```

### Production (Proposed)
```bash
# Weekly schedule (Sunday 2 AM UTC)
# Create: cron job or scheduled task
# Command: cd /platform/data-pipeline && python pipeline.py
```

---

## MONITORING & VALIDATION

### Pipeline Logs
```bash
# View recent execution
tail logs/pipeline.log

# View audit report
cat logs/audit_report.json | jq

# View full metadata
cat logs/pipeline_execution.json | jq
```

### Data Quality Checks
```bash
# Verify players dataset
python -c "
import pandas as pd
df = pd.read_csv('processed-data/master_players.csv')
print(f'✓ Players: {len(df)} rows')
print(f'✓ Countries: {df.country.nunique()} unique')
print(f'✓ Missing values: {df.isnull().sum().sum()} total')
print(f'✓ Form scores: {df.form_score.min():.2f}-{df.form_score.max():.2f}')
"

# Verify countries dataset
python -c "
import pandas as pd
df = pd.read_csv('processed-data/master_countries.csv')
print(f'✓ Countries: {len(df)} rows')
print(f'✓ Win rates: {df.win_rate.min():.2f}-{df.win_rate.max():.2f}')
print(f'✓ Recent form: {df.recent_form_score.min():.2f}-{df.recent_form_score.max():.2f}')
"
```

---

## TROUBLESHOOTING INTEGRATION

### Issue: Database file not found
**Solution**: 
```bash
# Ensure path exists
mkdir -p c:\FIFA WC\platform\backend-api\data
python pipeline.py  # This will create database
```

### Issue: "No module named 'data_pipeline'"
**Solution**:
```bash
# Add to Python path in FastAPI startup
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "data-pipeline"))
```

### Issue: Stale data in endpoints
**Solution**:
```bash
# Re-run pipeline to refresh
python pipeline.py

# Or manually refresh in FastAPI:
db.execute("DELETE FROM players")  # Clear old
db.commit()
# Then re-run pipeline
```

---

## NEXT STEPS FOR PHASE 2

### 1. Backend API Integration
- [ ] Create `IntelligenceRepository` to query processed data
- [ ] Create endpoints in `/api/v1/intelligence` 
- [ ] Add response schemas for players/countries/squads

### 2. Prediction Models
- [ ] Implement Elo rating system using `country_strength`
- [ ] Implement Poisson model using `goals_per_match`
- [ ] Train XGBoost on player features + form scores

### 3. Tournament Simulator
- [ ] Build simulator using squad aggregates
- [ ] Use form scores for match probability calculation
- [ ] Generate tournament brackets and predictions

### 4. Frontend Analytics
- [ ] Create player dashboard querying API
- [ ] Create country rankings using `attack_rating` + `defense_rating`
- [ ] Create match predictions using Elo/Poisson outputs

---

## IMPORTANT NOTES

### Data Freshness
- Pipeline should re-run weekly/monthly as new match data arrives
- Form scores are 2025-26 biased (recency weight = 0.5)
- Historical averages remain stable unless data is retroactively corrected

### Recency Bias (Critical for 2026)
```python
# Phase 1 weighted approach
form_score = (
    0.5 * recent_2025_26_matches +      # Half weight to recent
    0.3 * current_season_historical +    # Third to current season
    0.2 * historical_average             # Small historical component
)
```

This ensures predictions favor current form (important for 2026 WC).

### ML Model Training
All Phase 2 ML models should use:
- ✅ `form_score` (not raw goals) as feature
- ✅ `consistency_score` to detect streaky vs reliable performers
- ✅ `squad_strength` for team-level predictions
- ✅ `recent_form_score` to weight recent matches higher

---

**Last Updated**: May 7, 2026  
**Status**: Ready for Phase 2 Backend Integration ✅
