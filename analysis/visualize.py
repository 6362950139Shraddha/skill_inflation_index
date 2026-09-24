"""
visualize.py

Produces the headline charts for the project:
  1. Credential Inflation Index over time
  2. Component trends (years experience, skill count, % degree required, buzzwords)

Usage:
    python visualize.py --in ../output/index_by_quarter.csv --outdir ../output
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt


def plot_index(summary, outdir):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(summary["quarter"], summary["credential_inflation_index"],
            marker="o", linewidth=2, color="#c0392b")
    ax.axhline(100, linestyle="--", color="gray", linewidth=1, alpha=0.6)
    ax.set_title("Credential Inflation Index Over Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Quarter")
    ax.set_ylabel("Index (base 100 = first quarter)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    path = f"{outdir}/credential_inflation_index.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


def plot_components(summary, outdir):
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))

    axes[0, 0].plot(summary["quarter"], summary["avg_years_experience"], marker="o", color="#2980b9")
    axes[0, 0].set_title("Avg. Years Experience Required")
    axes[0, 0].tick_params(axis="x", rotation=45)

    axes[0, 1].plot(summary["quarter"], summary["avg_skill_count"], marker="o", color="#27ae60")
    axes[0, 1].set_title("Avg. Skill Count Required")
    axes[0, 1].tick_params(axis="x", rotation=45)

    axes[1, 0].plot(summary["quarter"], summary["pct_degree_required"], marker="o", color="#8e44ad")
    axes[1, 0].set_title("% Postings Requiring a Degree")
    axes[1, 0].tick_params(axis="x", rotation=45)

    axes[1, 1].plot(summary["quarter"], summary["avg_buzzword_count"], marker="o", color="#d35400")
    axes[1, 1].set_title("Avg. Scope-Creep Buzzword Count")
    axes[1, 1].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    path = f"{outdir}/component_trends.png"
    plt.savefig(path, dpi=150)
    plt.close()
    print(f"Saved: {path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="in_path", default="../output/index_by_quarter.csv")
    parser.add_argument("--outdir", default="../output")
    args = parser.parse_args()

    summary = pd.read_csv(args.in_path)
    plot_index(summary, args.outdir)
    plot_components(summary, args.outdir)


if __name__ == "__main__":
    main()
