#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-01-10 20:45:00 (ywatanabe)"
# File: /home/ywatanabe/proj/crossref_local/examples/impact_factor/02_compare_jcr_plot.py

"""
Plot Impact Factor Comparison: Calculated vs JCR

Uses scitex.plt for publication-quality figures.

Usage:
    python 02_compare_jcr_plot.py
"""

import json
from pathlib import Path

import numpy as np
import figrecipe as fr
from scipy import stats

# Load SCITEX style with white background
fr.load_style("SCITEX", background="white")

# Paths
INPUT_DIR = Path(__file__).parent / "01_compare_jcr_out"
OUTPUT_DIR = Path(__file__.replace(".py", "_out"))


def load_latest_results():
    """Load the comparison results."""
    json_path = INPUT_DIR / "all_combined.json"
    if not json_path.exists():
        raise FileNotFoundError(
            f"No results found at {json_path}. Run '01_compare_jcr.py --category all' first."
        )

    with open(json_path) as f:
        data = json.load(f)

    # Filter out only errors, keep all coverage levels to show discrepancies
    valid_data = [r for r in data if "error" not in r and r.get("jcr_if")]
    return valid_data


def plot_scatter_comparison(data, output_path):
    """Create scatter plot: Calculated IF vs JCR IF."""
    # Use figrecipe defaults
    fig, ax = fr.subplots()

    # Extract data
    calc_if = [r["calc_if"] for r in data if r.get("jcr_if")]
    jcr_if = [r["jcr_if"] for r in data if r.get("jcr_if")]
    names = [r["journal"][:20] for r in data if r.get("jcr_if")]

    # Calculate correlation
    r_pearson, p_pearson = stats.pearsonr(calc_if, jcr_if)
    r_spearman, p_spearman = stats.spearmanr(calc_if, jcr_if)

    # Scatter plot
    ax.scatter(jcr_if, calc_if)

    # Identity line
    max_val = max(max(calc_if), max(jcr_if)) * 1.1
    ax.plot([0, max_val], [0, max_val], "k--", alpha=0.5, label="y = x")

    # Regression line
    slope, intercept = np.polyfit(jcr_if, calc_if, 1)
    x_fit = np.linspace(0, max_val, 100)
    ax.plot(
        x_fit,
        slope * x_fit + intercept,
        "r-",
        alpha=0.7,
        label=f"Fit: y = {slope:.2f}x + {intercept:.2f}",
    )

    # Labels for high-IF journals
    for i, (x, y, name) in enumerate(zip(jcr_if, calc_if, names)):
        if x > 20 or y > 20:
            ax.annotate(
                name,
                (x, y),
                fontsize=6,
                alpha=0.8,
                xytext=(5, 5),
                textcoords="offset points",
            )

    ax.set_xlabel("JCR Impact Factor (2024)")
    ax.set_ylabel("Calculated Impact Factor\n(Local CrossRef)")
    ax.set_title("Impact Factor Comparison")
    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)

    # Add correlation text (6pt per SCITEX annotation style)
    text = f"Pearson r = {r_pearson:.3f}\nSpearman r = {r_spearman:.3f}\nn = {len(calc_if)}"
    ax.text(
        0.05,
        0.95,
        text,
        transform=ax.transAxes,
        verticalalignment="top",
        fontsize=6,
    )

    ax.legend(loc="lower right")

    # Set panel caption for composition (without panel letter - added during composition)
    ax.set_caption("Correlation between calculated and JCR Impact Factors")

    fr.save(fig, output_path, validate=False, verbose=False)
    print(f"Saved: {output_path}")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    print("Loading comparison data...")
    data = load_latest_results()
    print(f"Loaded {len(data)} journals with good coverage")

    print("\nGenerating plots...")

    # Scatter plot
    plot_scatter_comparison(data, OUTPUT_DIR / f"scatter_calc_vs_jcr.png")

    print(f"\nAll plots saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

# EOF
