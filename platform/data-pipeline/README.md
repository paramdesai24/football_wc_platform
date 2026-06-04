# Data Pipeline & Feature Engineering

The `data-pipeline` module cleans player statistics, performs name-entity resolution, computes Ratings System V2.1 features, and builds the SQLite database for backend consumption.

---

## 📈 Ratings V2.1 Calculations

The pipeline calculates the authoritative country metrics:

* **Attacking Rating (V2)**: Weighted combination of recent goal count (exponentially decayed), forward-line squad valuation, and international tournament ratings.
* **Defensive Rating (V2.1)**: Weighted combination of Z-score goals-conceded rate, clean sheet rate, backline valuation, and goalkeeper performance index.
* **Power Index**: Composite rank index:
  $$power\_index = 0.35 \times \text{elo} + 0.20 \times \text{attack} + 0.20 \times \text{defense} + 0.15 \times \text{squad} + 0.10 \times \text{form}$$
* **Elo Ratings**: Propagation of true Elo metrics from source files to final export assets, ensuring that New Zealand remains the sole team with fallback imputed $1500.0$.

---

## 📂 Layout

```markdown
platform/data-pipeline/
├── cleaning/             # Standardizes CSV formats, cleans player/country strings
├── feature_engineering/  # Calculates Attack/Defense V2.1 and Power Indexes
├── exports/             # Writes compiled datasets to PostgreSQL/SQLite schemas
├── utils/                # Registries, constants, and database maps
├── run_ratings_v2.py     # Main calculations runner
├── run_export.py         # Exports features to databases and sibling CSVs
└── README.md             # Pipeline README
```

---

## 🚀 Running Pipeline Tasks

1. Navigate to the pipeline directory:
   ```powershell
   cd platform/data-pipeline
   ```
2. Activate your virtual environment:
   ```powershell
   ..\.venv\Scripts\activate
   ```
3. Run rating features calculations:
   ```powershell
   python run_ratings_v2.py
   ```
4. Run DB/CSV export exporter:
   ```powershell
   python run_export.py
   ```
