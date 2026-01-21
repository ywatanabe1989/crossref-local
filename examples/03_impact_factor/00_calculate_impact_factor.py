#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-01-07 22:45:01 (ywatanabe)"
# File: /ssh:ywatanabe@nas:/home/ywatanabe/proj/crossref_local/examples/impact_factor/00_calculate_impact_factor.py


"""
Demo: Impact Factor Calculation

Example usage of the CrossRef Local impact factor calculator.
Compares calculated IF with OpenAlex IF proxy.

Usage:
    ./00_calculate_impact_factor.py --journal Nature --year 2023
    ./00_calculate_impact_factor.py --journal Science --year 2023 --duration 5
"""

import argparse
import sys
from pathlib import Path

# Add impact_factor to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "impact_factor"))
from src.calculator import ImpactFactorCalculator

DB_PATH = "./data/crossref.db"


def main():
    parser = argparse.ArgumentParser(
        description="Impact Factor Calculation Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --journal Nature --year 2023
  %(prog)s --journal "The Lancet" --year 2023
  %(prog)s --journal Science --year 2023 --duration 5
        """,
    )
    parser.add_argument(
        "--journal", default="Nature", help="Journal name (default: Nature)"
    )
    parser.add_argument(
        "--year", type=int, default=2023, help="Target year (default: 2023)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=2,
        help="Citation window in years (default: 2)",
    )
    parser.add_argument(
        "--db", default=DB_PATH, help="Path to CrossRef database"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Impact Factor Calculation")
    print("=" * 60)
    print()

    calc = ImpactFactorCalculator(args.db)

    # Lookup ISSN and OpenAlex IF proxy
    print(f"  Looking up: {args.journal}")
    issn = calc.get_journal_issn(args.journal)
    openalex_if = calc._journal_lookup.get_if_proxy(args.journal)
    journal_info = calc._journal_lookup.search(args.journal, limit=1)

    if issn:
        print(f"  ISSN: {issn}")
        identifier = issn
        use_issn = True
    else:
        print(f"  ISSN not found, using journal name (slower)")
        identifier = args.journal
        use_issn = False

    if openalex_if:
        print(f"  OpenAlex IF (2yr): {openalex_if:.2f}")

    if journal_info:
        info = journal_info[0]
        if info.get("h_index"):
            print(f"  OpenAlex h-index: {info['h_index']}")
        if info.get("works_count"):
            print(f"  OpenAlex works: {info['works_count']:,}")

    print()
    print(f"  Calculating {args.duration}-year IF for {args.year}...")
    print()

    result = calc.calculate_impact_factor(
        journal_identifier=identifier,
        target_year=args.year,
        window_years=args.duration,
        use_issn=use_issn,
        method="citations-table",  # Fast, year-specific using indexed citations table
        citable_only=True,  # Only count citable items (research articles) per JCR methodology
    )

    print("-" * 60)
    print(f"  Journal:           {args.journal}")
    if issn:
        print(f"  ISSN:              {issn}")
    print(f"  Target Year:       {result['target_year']}")
    print(f"  Window:            {result['window_range']}")
    print(f"  Citable Items:     {result['total_articles']:,}")
    print(f"  Citations:         {result['total_citations']:,}")
    print("-" * 60)
    print(f"  Calculated IF:     {result['impact_factor']:.2f}")
    if openalex_if:
        print(f"  OpenAlex IF:       {openalex_if:.2f}")
    print("-" * 60)
    print()

    # Show methodology note
    print("  Note: Uses JCR methodology - citable items only (>20 refs)")
    print("  excludes news, editorials, letters, corrections")
    print()
    print("=" * 60)

    calc.close()


if __name__ == "__main__":
    main()

# EOF
