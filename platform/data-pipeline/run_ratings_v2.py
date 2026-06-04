"""
Rating System 2.0 — Standalone Runner

Generates attack_rating_v2 and defense_rating_v2 for all prediction-eligible
teams. Writes comparison tables, component distributions, correlation matrix,
and per-team JSON breakdowns.

Does NOT overwrite production ratings. Outputs are parallel files only.
"""

import sys
import io
# Use UTF-8 for stdout to handle non-ASCII country names and icons
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import logging
import textwrap
from pathlib import Path

# Ensure pipeline root is on sys.path when run directly
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from utils.logging_utils import setup_logger
from feature_engineering.ratings_v2 import (
    load_inputs,
    compute_v2_ratings,
    validate_v2,
    export_all,
    build_component_distribution,
    build_correlation_matrix,
)

logger = setup_logger("ratings_v2", "ratings_v2.log")


def print_comparison_table(df, sort_col: str, v1_col: str, v2_col: str, title: str, n: int = 25) -> None:
    """Print a ranked comparison table."""
    ranked = df.sort_values(v2_col, ascending=False).reset_index(drop=True)
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")
    print(f"  {'Rank':<5} {'Country':<24} {'v1':>7} {'v2':>7} {'Delta':>8}  {'Comp A':>7} {'Comp B':>7} {'Comp C':>7} {'Comp D':>7}")
    print(f"  {'-'*5} {'-'*24} {'-'*7} {'-'*7} {'-'*8}  {'-'*7} {'-'*7} {'-'*7} {'-'*7}")

    comp_a_col  = "comp_recency_attack"  if "attack" in v2_col else "comp_recency_defense"
    comp_b_col  = "comp_squad_attack"    if "attack" in v2_col else "comp_squad_defense"

    for i, row in ranked.head(n).iterrows():
        rank  = i + 1
        name  = str(row["country_name"])[:23]
        v1    = float(row[v1_col])
        v2    = float(row[v2_col])
        delta = v2 - v1
        a     = float(row[comp_a_col])
        b     = float(row[comp_b_col])
        c     = float(row["comp_elo"])
        d     = float(row["comp_form"])
        delta_sign = "+" if delta >= 0 else ""
        print(f"  {rank:<5} {name:<24} {v1:>7.1f} {v2:>7.1f} {delta_sign}{delta:>7.1f}  {a:>7.1f} {b:>7.1f} {c:>7.1f} {d:>7.1f}")


def print_distribution(df) -> None:
    """Print component distribution diagnostics."""
    dist = build_component_distribution(df)
    print(f"\n{'=' * 70}")
    print("  COMPONENT DISTRIBUTION (reveals variance & contribution)")
    print(f"{'=' * 70}")
    print(f"  {'Component':<22} {'Min':>7} {'P10':>7} {'P25':>7} {'Med':>7} {'P75':>7} {'P90':>7} {'Max':>7} {'Std':>7}")
    print(f"  {'-'*22} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7} {'-'*7}")
    for _, row in dist.iterrows():
        print(
            f"  {str(row['component']):<22} {row['min']:>7.1f} {row['p10']:>7.1f} "
            f"{row['p25']:>7.1f} {row['median']:>7.1f} {row['p75']:>7.1f} "
            f"{row['p90']:>7.1f} {row['max']:>7.1f} {row['std']:>7.1f}"
        )


def print_correlation(df) -> None:
    """Print correlation matrix between key metrics."""
    corr = build_correlation_matrix(df)
    print(f"\n{'=' * 70}")
    print("  CORRELATION MATRIX")
    print(f"{'=' * 70}")
    print(corr.to_string())


def print_spot_checks(df) -> None:
    """Spot-check key teams."""
    targets = ["Spain", "France", "Germany", "Brazil", "Argentina",
               "Japan", "Morocco", "England", "Italy", "Netherlands"]
    atk = df.sort_values("attack_rating_v2", ascending=False).reset_index(drop=True)
    atk["atk_rank"] = atk.index + 1
    def_ = df.sort_values("defense_rating_v2", ascending=False).reset_index(drop=True)
    def_["def_rank"] = def_.index + 1
    merged = atk[["country_name","atk_rank","attack_v1","attack_rating_v2"]].merge(
        def_[["country_name","def_rank","defense_v1","defense_rating_v2"]],
        on="country_name"
    )

    print(f"\n{'=' * 70}")
    print("  SPOT CHECKS — KEY NATIONS")
    print(f"{'=' * 70}")
    print(f"  {'Country':<22} {'Atk Rank':>9} {'Atk v1':>8} {'Atk v2':>8}  {'Def Rank':>9} {'Def v1':>8} {'Def v2':>8}")
    print(f"  {'-'*22} {'-'*9} {'-'*8} {'-'*8}  {'-'*9} {'-'*8} {'-'*8}")
    for _, row in merged[merged["country_name"].isin(targets)].iterrows():
        print(
            f"  {str(row['country_name']):<22} {int(row['atk_rank']):>9} "
            f"{float(row['attack_v1']):>8.1f} {float(row['attack_rating_v2']):>8.1f}  "
            f"{int(row['def_rank']):>9} {float(row['defense_v1']):>8.1f} {float(row['defense_rating_v2']):>8.1f}"
        )


def main():
    logger.info("=" * 60)
    logger.info("Rating System 2.0 — Starting")
    logger.info("=" * 60)

    # ── Load inputs ──────────────────────────────────────────────────────────
    print("\nLoading data...")
    rankings_df, results_df, master_players, fbref_df = load_inputs()
    print(f"  Rankings: {len(rankings_df)} countries ({(rankings_df['prediction_eligible']==True).sum()} eligible)")
    print(f"  Match results: {len(results_df)} rows")
    print(f"  Master players: {len(master_players)} rows")
    print(f"  FBRef 2025/26: {len(fbref_df)} rows")

    # ── Compute v2 ratings ───────────────────────────────────────────────────
    print("\nComputing v2 ratings (this may take ~30s)...")
    df = compute_v2_ratings(rankings_df, results_df, master_players, fbref_df)
    print(f"  Done. Computed ratings for {len(df)} teams.")

    # ── Validate ─────────────────────────────────────────────────────────────
    print("\nRunning validation...")
    warnings = validate_v2(df)
    if warnings:
        print(f"\n  {len(warnings)} WARNING(s):")
        for w in warnings:
            print(f"    {w}")
            logger.warning(w)
    else:
        print("  All validation checks passed.")

    # ── Print reports ─────────────────────────────────────────────────────────
    print_comparison_table(df, "attack_rating_v2", "attack_v1", "attack_rating_v2",
                            "ATTACK RATING: v1 vs v2 (top 25)")
    print_comparison_table(df, "defense_rating_v2", "defense_v1", "defense_rating_v2",
                            "DEFENSE RATING: v1 vs v2 (top 25)")
    print_spot_checks(df)
    print_distribution(df)
    print_correlation(df)

    # ── Export ───────────────────────────────────────────────────────────────
    print("\nWriting output files...")
    export_all(df)
    print("\n  Output files written to platform/data/processed/:")
    print("    attack_defense_ratings_v2_comparison.csv")
    print("    attack_defense_v2_components.csv")
    print("    component_distribution.csv")
    print("    correlation_matrix.csv")
    print("    attack_breakdown.json")
    print("    defense_breakdown.json")

    print(f"\n{'=' * 70}")
    print("  Rating System 2.0 complete. Production ratings UNCHANGED.")
    print("  Review output then run promotion step to go live.")
    print(f"{'=' * 70}\n")
    logger.info("Rating System 2.0 complete.")


if __name__ == "__main__":
    main()
