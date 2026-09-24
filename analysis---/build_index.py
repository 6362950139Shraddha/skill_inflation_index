"""
build_index.py

Aggregates extracted features by time period (quarter) and builds a
composite "Credential Inflation Index" — a single normalized score (base
100 at the earliest period) that tracks how much harder it's gotten to
qualify for the role over time.

Components (each z-scored, then combined with equal weight by default):
  - avg years of experience required
  - avg skill count required
  - % of postings requiring a degree (Bachelor's or Master's "required")
  - avg buzzword count (proxy for scope creep / soft-requirement inflation)

Usage:
    python build_index.py --in ../output/features.csv \
        --out ../output/index_by_quarter.csv
"""

import argparse
import pandas as pd
import numpy as np


def pct_degree_required(series):
    return (series.isin(["Bachelor's required", "Master's required"])).mean() * 100


def build_quarterly_summary(df):
    grouped = df.groupby("quarter").agg(
        n_postings=("description", "count"),
        avg_years_experience=("years_experience_extracted", "mean"),
        avg_skill_count=("skill_count_extracted", "mean"),
        pct_degree_required=("degree_level_extracted", pct_degree_required),
        avg_buzzword_count=("buzzword_count", "mean"),
    ).reset_index()

    # Sort chronologically (assumes quarter strings like "2022Q1")
    grouped["sort_key"] = grouped["quarter"].apply(
        lambda q: int(q[:4]) * 4 + int(q[-1])
    )
    grouped = grouped.sort_values("sort_key").drop(columns="sort_key").reset_index(drop=True)
    return grouped


def zscore(series):
    return (series - series.mean()) / series.std(ddof=0)


def build_composite_index(summary, weights=None):
    """
    Combine the four component metrics into a single index, base-100 at the
    first period. weights: optional dict to weight components unequally,
    e.g. {'avg_years_experience': 2, 'avg_skill_count': 1, ...}
    """
    components = [
        "avg_years_experience", "avg_skill_count",
        "pct_degree_required", "avg_buzzword_count",
    ]
    if weights is None:
        weights = {c: 1.0 for c in components}

    z = summary[components].apply(zscore)
    weighted_sum = sum(z[c] * weights[c] for c in components) / sum(weights.values())

    # Rescale so the first period = 100, with the composite trend applied
    # relative to the average variation observed (keeps the index interpretable)
    scale = 10  # controls how many "points" one std dev of drift is worth
    raw_index = 100 + (weighted_sum - weighted_sum.iloc[0]) * scale

    summary = summary.copy()
    summary["credential_inflation_index"] = raw_index.round(1)
    return summary


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", default="../output/features.csv")
    parser.add_argument("--out", dest="out_path", default="../output/index_by_quarter.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.in_path)
    summary = build_quarterly_summary(df)
    summary = build_composite_index(summary)

    summary.to_csv(args.out_path, index=False)
    print(f"Built index for {len(summary)} quarters -> {args.out_path}\n")
    print(summary.to_string(index=False))

    first, last = summary.iloc[0], summary.iloc[-1]
    print(f"\nHeadline finding: Credential Inflation Index moved from "
          f"{first['credential_inflation_index']:.1f} in {first['quarter']} "
          f"to {last['credential_inflation_index']:.1f} in {last['quarter']} "
          f"({last['credential_inflation_index'] - first['credential_inflation_index']:+.1f} pts).")


if __name__ == "__main__":
    main()
