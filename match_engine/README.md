# Match Simulation Engine 🧠

The `match_engine` is the mathematical core responsible for head-to-head score forecasting, win probability modeling, and match outcomes simulation.

---

## 🔮 Core Functionality

1. **Probability Engine**: Compares the dynamic metrics of any two teams (Elo ratings, V2.1 Attack and Defense ratings, recent form, and squad values) to calculate a composite win/draw/loss margin.
2. **Poisson Score Generation**: Uses team ratings to calculate goal expectancy parameter $\lambda$ for each country, then samples scores from a Poisson distribution.
3. **Stochastic and Non-Stochastic Overrides**: Offers deterministic baseline prediction runs as well as stochastic (randomized simulation) modeling runs.
4. **Realism Constraints**: Enforces tournament limits (e.g. extra time, penalties, knockout resolution rules) to ensure outputs mirror FIFA World Cup standards.

---

## 📂 Layout

```markdown
match_engine/
├── utils/
│   ├── data_loader.py    # Merges team metrics, active Elo databases, and mappings
│   └── simulator.py     # Main Poisson distribution calculator and match generator
└── README.md             # Engine overview
```

---

## ⚙️ Mathematical Model

The score simulation computes expected goals for the Home team (g_H) and Away team (g_A) based on:

```text
g_H = lambda_H * elo_advantage * attack_advantage
g_A = lambda_A * elo_disadvantage * defense_advantage
```

These expected values parameters (lambda) are then sampled:

```text
Goals ~ Poisson(lambda)
```

This structure guarantees that quality differences are translated into realistic scoring probabilities while maintaining the unpredictability of cup football.
