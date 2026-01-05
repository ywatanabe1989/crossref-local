#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-10-12 03:18:28 (ywatanabe)"
# File: /mnt/nas_ug/crossref_local/impact_factor/calculate_if.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./impact_factor/calculate_if.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------
"""
CLI tool for calculating journal impact factors from CrossRef local database.

Usage:
    python calculate_if.py --journal "Nature" --year 2023
    python calculate_if.py --journal "Nature" --year 2020-2024 --moving-avg 3
    python calculate_if.py --issn "0028-0836" --year 2023 --method reference-graph
    python calculate_if.py --journal-file journals.txt --year 2023 --output results.csv
"""

import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import List

# Add parent directory to path to import from src/
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.calculator import ImpactFactorCalculator

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def parse_year_range(year_str: str) -> tuple:
    """
    Parse year or year range.

    Args:
        year_str: Single year "2023" or range "2020-2024"

    Returns:
        Tuple of (start_year, end_year)
    """
    if "-" in year_str:
        start, end = year_str.split("-")
        return int(start), int(end)
    else:
        year = int(year_str)
        return year, year


def read_journal_list(file_path: str) -> List[str]:
    """
    Read journal names from file.

    Args:
        file_path: Path to text file with one journal per line

    Returns:
        List of journal names
    """
    with open(file_path, "r") as f:
        journals = [line.strip() for line in f if line.strip()]
    return journals


def format_result_text(result: dict) -> str:
    """
    Format result as human-readable text.

    Args:
        result: Result dictionary from calculator

    Returns:
        Formatted string
    """
    lines = [
        "=" * 70,
        f"Journal: {result['journal']}",
        f"Target Year: {result['target_year']}",
        f"Window: {result['window_range']} ({result['window_years']} years)",
        f"Method: {result['method']}",
        "-" * 70,
        f"Articles published in window: {result['total_articles']}",
    ]

    if result.get("articles_by_year"):
        lines.append("  By year:")
        for year, count in sorted(result["articles_by_year"].items()):
            lines.append(f"    {year}: {count} articles")

    lines.extend(
        [
            "-" * 70,
            f"Citations to window articles: {result['total_citations']}",
            f"Impact Factor: {result['impact_factor']:.3f}",
        ]
    )

    if result.get("moving_average") is not None:
        lines.append(f"Moving Average: {result['moving_average']:.3f}")

    lines.append("=" * 70)

    return "\n".join(lines)


def write_results_csv(results: List[dict], output_path: str):
    """
    Write results to CSV file.

    Args:
        results: List of result dictionaries
        output_path: Output CSV path
    """
    if not results:
        logger.warning("No results to write")
        return

    fieldnames = [
        "journal",
        "target_year",
        "window_years",
        "window_range",
        "total_articles",
        "total_citations",
        "impact_factor",
        "moving_average",
        "method",
        "status",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=fieldnames, extrasaction="ignore"
        )
        writer.writeheader()

        for result in results:
            # Flatten articles_by_year for CSV
            result_copy = result.copy()
            if "articles_by_year" in result_copy:
                del result_copy["articles_by_year"]
            writer.writerow(result_copy)

    logger.info(f"Results written to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Calculate journal impact factors from CrossRef local database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single journal, single year
  %(prog)s --journal "Nature" --year 2023

  # Single journal, year range with moving average
  %(prog)s --journal "Nature" --year 2020-2024 --moving-avg 3

  # Use ISSN for precise matching
  %(prog)s --issn "0028-0836" --year 2023

  # Use reference-graph method (slower but more accurate)
  %(prog)s --journal "Nature" --year 2023 --method reference-graph

  # Calculate 5-year impact factor
  %(prog)s --journal "Nature" --year 2023 --window 5

  # Batch process multiple journals
  %(prog)s --journal-file journals.txt --year 2023 --output results.csv

  # Batch with year range
  %(prog)s --journal-file journals.txt --year 2020-2024 --output results.csv
        """,
    )

    # Journal identification
    journal_group = parser.add_mutually_exclusive_group(required=True)
    journal_group.add_argument(
        "--journal", type=str, help='Journal name (e.g., "Nature")'
    )
    journal_group.add_argument(
        "--issn", type=str, help='Journal ISSN (e.g., "0028-0836")'
    )
    journal_group.add_argument(
        "--journal-file",
        type=str,
        help="File with journal names (one per line)",
    )

    # Year specification
    parser.add_argument(
        "--year",
        type=str,
        required=True,
        help='Year or year range (e.g., "2023" or "2020-2024")',
    )

    # Calculation parameters
    parser.add_argument(
        "--window",
        type=int,
        default=2,
        choices=[2, 5],
        help="Citation window in years (default: 2 for 2-year IF)",
    )

    parser.add_argument(
        "--method",
        type=str,
        default="is-referenced-by",
        choices=["is-referenced-by", "reference-graph"],
        help="Citation counting method (default: is-referenced-by)",
    )

    parser.add_argument(
        "--moving-avg",
        type=int,
        metavar="N",
        help="Calculate N-year moving average (only for year ranges)",
    )

    # Database
    parser.add_argument(
        "--db",
        type=str,
        default="./data/crossref.db",
        help="Path to CrossRef database (default: ./data/crossref.db)",
    )

    # Output
    parser.add_argument(
        "--output",
        type=str,
        help="Output CSV file path (default: print to stdout)",
    )

    parser.add_argument(
        "--verbose", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Parse year range
    start_year, end_year = parse_year_range(args.year)

    # Get journal list
    if args.journal_file:
        journals = read_journal_list(args.journal_file)
        use_issn = False
    elif args.issn:
        journals = [args.issn]
        use_issn = True
    else:
        journals = [args.journal]
        use_issn = False

    # Calculate impact factors
    all_results = []

    with ImpactFactorCalculator(db_path=args.db) as calc:
        for journal in journals:
            logger.info(f"\nProcessing: {journal}")

            if start_year == end_year:
                # Single year
                result = calc.calculate_impact_factor(
                    journal_identifier=journal,
                    target_year=start_year,
                    window_years=args.window,
                    use_issn=use_issn,
                    method=args.method,
                )
                all_results.append(result)

                if not args.output:
                    print(format_result_text(result))

            else:
                # Year range
                results = calc.calculate_if_time_series(
                    journal_identifier=journal,
                    start_year=start_year,
                    end_year=end_year,
                    window_years=args.window,
                    use_issn=use_issn,
                    method=args.method,
                )

                # Calculate moving average if requested
                if args.moving_avg:
                    results = calc.calculate_moving_average(
                        results, window=args.moving_avg
                    )

                all_results.extend(results)

                if not args.output:
                    for result in results:
                        print(format_result_text(result))

    # Write output if requested
    if args.output:
        write_results_csv(all_results, args.output)
        logger.info(
            f"\nProcessed {len(journals)} journal(s), {len(all_results)} calculation(s)"
        )
    else:
        logger.info(
            f"\nCompleted: {len(journals)} journal(s), {len(all_results)} calculation(s)"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())

# EOF
