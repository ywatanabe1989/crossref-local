#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-01-07 22:37:13 (ywatanabe)"
# File: /ssh:ywatanabe@nas:/home/ywatanabe/proj/crossref_local/examples/impact_factor/01_compare_jcr.py


"""
Compare Calculated Impact Factors with JCR Official Values

Validates our CrossRef-based IF calculation against Clarivate JCR data.
Results are saved to compare_jcr_out/ directory.

Usage:
    python 01_compare_jcr.py
    python 01_compare_jcr.py --category neuroscience
    python 01_compare_jcr.py --category all
"""

import argparse
import csv
import json
import sys
from pathlib import Path

import pandas as pd

# Add impact_factor to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "impact_factor"))
from src.calculator import ImpactFactorCalculator

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "data" / "crossref.db"
jcr_PATH = PROJECT_ROOT / "GITIGNORED" / "jcr_impact_factor_2024.xlsx"
OUTPUT_DIR = Path(__file__.replace(".py", "_out"))

# Journal categories
JOURNALS = {
    "neuroscience": [
        ("Nature Reviews Neuroscience", "1471-003X"),
        ("Nature Neuroscience", "1097-6256"),
        ("Neuron", "0896-6273"),
        ("Trends in Neurosciences", "0166-2236"),
        ("Annual Review of Neuroscience", "0147-006X"),
        ("Brain", "0006-8950"),
        ("Molecular Psychiatry", "1359-4184"),
        ("Biological Psychiatry", "0006-3223"),
        ("Progress in Neurobiology", "0301-0082"),
        ("Current Opinion in Neurobiology", "0959-4388"),
        ("NeuroImage", "1053-8119"),
        ("Cerebral Cortex", "1047-3211"),
        ("Journal of Neurophysiology", "0022-3077"),
        ("Frontiers in Neuroscience", "1662-453X"),
        ("Journal of Neuroscience", "0270-6474"),
        ("Neuropsychopharmacology", "0893-133X"),
        ("Brain Stimulation", "1935-861X"),
        ("eLife", "2050-084X"),
    ],
    "biomedical_engineering": [
        ("Nature Biomedical Engineering", "2157-846X"),
        ("Biomaterials", "0142-9612"),
        ("Journal of Neural Engineering", "1741-2552"),
        ("IEEE Trans Biomedical Engineering", "0018-9294"),
        ("IEEE Trans Neural Syst Rehabil Eng", "1534-4320"),
        ("Biomedical Engineering Online", "1475-925X"),
    ],
    "high_impact": [
        ("Nature", "0028-0836"),
        ("Science", "0036-8075"),
        ("Cell", "0092-8674"),
        ("The Lancet", "0140-6736"),
        ("New England Journal of Medicine", "0028-4793"),
        ("JAMA", "0098-7484"),
        ("Nature Medicine", "1078-8956"),
        ("Nature Communications", "2041-1723"),
        ("PNAS", "0027-8424"),
    ],
}


def load_jcr_data():
    """Load JCR Impact Factor data."""
    jcr = pd.read_excel(jcr_PATH)
    jcr["ISSN"] = jcr["ISSN"].astype(str).str.strip()
    jcr["EISSN"] = jcr["EISSN"].astype(str).str.strip()
    jcr["JIF"] = pd.to_numeric(jcr["JIF"], errors="coerce")
    return jcr


def get_jcr_if(jcr_df, issn):
    """Look up JCR IF by ISSN or EISSN."""
    match = jcr_df[(jcr_df["ISSN"] == issn) | (jcr_df["EISSN"] == issn)]
    if len(match) > 0:
        return float(match.iloc[0]["JIF"]), match.iloc[0]["Name"]
    return None, None


def calculate_coverage(calc, issn):
    """Calculate citation coverage percentage."""
    dois = calc.get_article_dois(issn, 2021, use_issn=True, citable_only=True)
    dois += calc.get_article_dois(issn, 2022, use_issn=True, citable_only=True)
    if not dois:
        return 0.0
    cites_table = calc._count_citations_from_table(dois, 2023)
    cites_cumul = calc._count_citations_simple(dois, 2023)
    return (cites_table / cites_cumul * 100) if cites_cumul > 0 else 0.0


def compare_journals(journals, calc, jcr_df, target_year=2023):
    """Compare calculated IF with JCR for a list of journals."""
    results = []

    for journal_name, issn in journals:
        try:
            jcr_if, jcr_name = get_jcr_if(jcr_df, issn)
            openalex_if = calc._journal_lookup.get_if_proxy(journal_name) or 0

            result = calc.calculate_impact_factor(
                journal_identifier=issn,
                target_year=target_year,
                window_years=2,
                use_issn=True,
                method="citations-table",
                citable_only=True,
            )

            calc_if = result["impact_factor"]
            items = result["total_articles"]
            citations = result["total_citations"]
            coverage = calculate_coverage(calc, issn)

            # Determine match quality
            if jcr_if and jcr_if > 0 and calc_if > 0:
                ratio = calc_if / jcr_if
                if 0.7 <= ratio <= 1.5:
                    match = "good"
                elif 0.3 <= ratio < 0.7:
                    match = "moderate"
                else:
                    match = "poor"
            else:
                ratio = None
                match = "no_jcr"

            results.append(
                {
                    "journal": journal_name,
                    "issn": issn,
                    "citable_items": items,
                    "citations": citations,
                    "calc_if": round(calc_if, 2),
                    "jcr_if": round(jcr_if, 1) if jcr_if else None,
                    "openalex_if": (
                        round(openalex_if, 2) if openalex_if else None
                    ),
                    "ratio": round(ratio, 2) if ratio else None,
                    "coverage_pct": round(coverage, 1),
                    "match": match,
                }
            )

        except Exception as e:
            results.append(
                {
                    "journal": journal_name,
                    "issn": issn,
                    "error": str(e),
                }
            )

    return results


def save_results(results, category, output_dir):
    """Save results to CSV and JSON files."""
    # CSV output
    csv_path = output_dir / f"{category}.csv"
    with open(csv_path, "w", newline="") as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    print(f"  Saved: {csv_path}")

    # JSON output
    json_path = output_dir / f"{category}.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Saved: {json_path}")

    return csv_path, json_path


def print_summary(results, category):
    """Print summary table to console."""
    print()
    print("=" * 100)
    print(f"  {category.upper()} - Impact Factor Comparison (2023)")
    print("=" * 100)
    print()

    # Split by coverage
    good = [
        r
        for r in results
        if r.get("coverage_pct", 0) > 10 and "error" not in r
    ]
    poor = [
        r
        for r in results
        if r.get("coverage_pct", 0) <= 10 and "error" not in r
    ]

    if good:
        print("  Journals with Good Citation Coverage (>10%):")
        print("-" * 100)
        print(
            f"{'Journal':<40} {'Calc IF':>10} {'JCR IF':>10} {'Ratio':>8} {'Match':>8}"
        )
        print("-" * 100)

        for r in sorted(good, key=lambda x: -(x.get("jcr_if") or 0)):
            jcr_str = f"{r['jcr_if']:.1f}" if r.get("jcr_if") else "N/A"
            ratio_str = f"{r['ratio']:.2f}" if r.get("ratio") else "N/A"
            match_icon = {
                "good": "OK",
                "moderate": "~",
                "poor": "X",
                "no_jcr": "-",
            }.get(r.get("match", ""), "?")
            print(
                f"{r['journal']:<40} {r['calc_if']:>10.2f} {jcr_str:>10} {ratio_str:>8} {match_icon:>8}"
            )

    if poor:
        print()
        print(
            "  Journals with Low Citation Coverage (<10%) - USE WITH CAUTION:"
        )
        print("-" * 100)
        print(
            f"{'Journal':<40} {'Coverage':>10} {'Calc IF':>10} {'JCR IF':>10}"
        )
        print("-" * 100)

        for r in poor:
            jcr_str = f"{r['jcr_if']:.1f}" if r.get("jcr_if") else "N/A"
            print(
                f"{r['journal']:<40} {r['coverage_pct']:>9.1f}% {r['calc_if']:>10.2f} {jcr_str:>10}"
            )

    print()


def main():
    parser = argparse.ArgumentParser(description="Compare IF with JCR")
    parser.add_argument(
        "--category",
        choices=list(JOURNALS.keys()) + ["all"],
        default="neuroscience",
        help="Journal category to test",
    )
    parser.add_argument(
        "--year", type=int, default=2023, help="Target year for IF calculation"
    )
    args = parser.parse_args()

    # Setup
    OUTPUT_DIR.mkdir(exist_ok=True)
    jcr_df = load_jcr_data()
    calc = ImpactFactorCalculator(str(DB_PATH))

    # Determine categories to process
    if args.category == "all":
        categories = list(JOURNALS.keys())
    else:
        categories = [args.category]

    # Process each category
    all_results = []
    for category in categories:
        journals = JOURNALS[category]
        results = compare_journals(journals, calc, jcr_df, args.year)
        all_results.extend(results)

        print_summary(results, category)
        save_results(results, category, OUTPUT_DIR)

    # Save combined results if multiple categories
    if len(categories) > 1:
        save_results(all_results, "all_combined", OUTPUT_DIR)

    calc.close()
    print(f"\nResults saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

# EOF
