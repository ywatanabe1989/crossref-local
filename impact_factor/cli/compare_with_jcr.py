#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compare calculated impact factors with official JCR data.

Usage:
    python compare_with_jcr.py --journal "Nature" --year 2023 --jcr-db /path/to/jcr.db
    python compare_with_jcr.py --journal-file journals.txt --year 2023 --jcr-db /path/to/jcr.db --output comparison.csv
"""

import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
from scipy import stats

# Add parent directory to path to import from src/
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.calculator import ImpactFactorCalculator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_jcr_impact_factor(journal_name: str, jcr_db_path: str) -> Optional[float]:
    """
    Get official JCR impact factor from database.

    Args:
        journal_name: Journal name
        jcr_db_path: Path to JCR database

    Returns:
        Impact factor or None if not found
    """
    import sqlite3

    try:
        conn = sqlite3.connect(jcr_db_path)
        cursor = conn.execute(
            """
            SELECT factor FROM factor
            WHERE LOWER(journal) LIKE LOWER(?)
            LIMIT 1
            """,
            (f"%{journal_name}%",)
        )
        result = cursor.fetchone()
        conn.close()

        return float(result[0]) if result else None
    except Exception as e:
        logger.error(f"Error accessing JCR database: {e}")
        return None


def compare_results(
    calculated_if: float,
    jcr_if: Optional[float]
) -> Dict:
    """
    Compare calculated IF with JCR official IF.

    Args:
        calculated_if: Calculated impact factor
        jcr_if: Official JCR impact factor

    Returns:
        Dictionary with comparison metrics
    """
    if jcr_if is None:
        return {
            'jcr_if': None,
            'difference': None,
            'percent_difference': None,
            'status': 'jcr_not_found'
        }

    difference = calculated_if - jcr_if
    percent_diff = (difference / jcr_if * 100) if jcr_if != 0 else None

    return {
        'jcr_if': jcr_if,
        'difference': difference,
        'percent_difference': percent_diff,
        'status': 'compared'
    }


def format_comparison_text(journal: str, result: Dict) -> str:
    """
    Format comparison as human-readable text.

    Args:
        journal: Journal name
        result: Comparison result dictionary

    Returns:
        Formatted string
    """
    lines = [
        "=" * 70,
        f"Journal: {journal}",
        f"Year: {result.get('target_year', 'N/A')}",
        "-" * 70,
        f"Calculated IF: {result['calculated_if']:.3f}",
        f"Official JCR IF: {result['jcr_if']:.3f}" if result['jcr_if'] else "Official JCR IF: Not found",
    ]

    if result.get('difference') is not None:
        diff_sign = '+' if result['difference'] >= 0 else ''
        lines.extend([
            f"Difference: {diff_sign}{result['difference']:.3f}",
            f"Percent Difference: {diff_sign}{result['percent_difference']:.1f}%"
        ])

        # Add interpretation
        abs_percent = abs(result['percent_difference'])
        if abs_percent < 5:
            lines.append("Status: ✓ Excellent agreement")
        elif abs_percent < 10:
            lines.append("Status: ~ Good agreement")
        elif abs_percent < 20:
            lines.append("Status: ! Moderate difference")
        else:
            lines.append("Status: ✗ Large difference")

    lines.append("=" * 70)

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compare calculated impact factors with official JCR data",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Journal identification
    journal_group = parser.add_mutually_exclusive_group(required=True)
    journal_group.add_argument(
        '--journal',
        type=str,
        help='Journal name (e.g., "Nature")'
    )
    journal_group.add_argument(
        '--journal-file',
        type=str,
        help='File with journal names (one per line)'
    )

    # Year specification
    parser.add_argument(
        '--year',
        type=int,
        required=True,
        help='Year for comparison'
    )

    # Database paths
    parser.add_argument(
        '--crossref-db',
        type=str,
        default='/mnt/nas_ug/crossref_local/data/crossref.db',
        help='Path to CrossRef database'
    )

    parser.add_argument(
        '--jcr-db',
        type=str,
        required=True,
        help='Path to JCR impact factor database'
    )

    # Calculation parameters
    parser.add_argument(
        '--window',
        type=int,
        default=2,
        choices=[2, 5],
        help='Citation window in years (default: 2)'
    )

    parser.add_argument(
        '--method',
        type=str,
        default='is-referenced-by',
        choices=['is-referenced-by', 'reference-graph'],
        help='Citation counting method'
    )

    # Output
    parser.add_argument(
        '--output',
        type=str,
        help='Output CSV file path'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Get journal list
    if args.journal_file:
        with open(args.journal_file, 'r') as f:
            journals = [line.strip() for line in f if line.strip()]
    else:
        journals = [args.journal]

    # Compare impact factors
    all_comparisons = []

    with ImpactFactorCalculator(db_path=args.crossref_db) as calc:
        for journal in journals:
            logger.info(f"\nProcessing: {journal}")

            # Calculate IF
            calc_result = calc.calculate_impact_factor(
                journal_identifier=journal,
                target_year=args.year,
                window_years=args.window,
                method=args.method
            )

            # Get JCR IF
            jcr_if = get_jcr_impact_factor(journal, args.jcr_db)

            # Compare
            comparison = compare_results(
                calculated_if=calc_result['impact_factor'],
                jcr_if=jcr_if
            )

            # Combine results
            result = {
                'journal': journal,
                'target_year': args.year,
                'calculated_if': calc_result['impact_factor'],
                'total_articles': calc_result['total_articles'],
                'total_citations': calc_result['total_citations'],
                **comparison
            }

            all_comparisons.append(result)

            if not args.output:
                print(format_comparison_text(journal, result))

    # Write output if requested
    if args.output:
        fieldnames = [
            'journal',
            'target_year',
            'calculated_if',
            'jcr_if',
            'difference',
            'percent_difference',
            'total_articles',
            'total_citations',
            'status'
        ]

        with open(args.output, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_comparisons)

        logger.info(f"\nComparison results written to {args.output}")

    # Summary statistics with correlation
    compared_count = sum(1 for r in all_comparisons if r['status'] == 'compared')
    if compared_count > 0:
        # Calculate correlation
        calc_ifs = [r['calculated_if'] for r in all_comparisons if r['jcr_if'] is not None]
        jcr_ifs = [r['jcr_if'] for r in all_comparisons if r['jcr_if'] is not None]

        if len(calc_ifs) >= 3:  # Need at least 3 points for meaningful correlation
            pearson_r, pearson_p = stats.pearsonr(calc_ifs, jcr_ifs)
            spearman_r, spearman_p = stats.spearmanr(calc_ifs, jcr_ifs)

            # Mean absolute error
            mae = np.mean([abs(c - j) for c, j in zip(calc_ifs, jcr_ifs)])

            # Root mean square error
            rmse = np.sqrt(np.mean([(c - j)**2 for c, j in zip(calc_ifs, jcr_ifs)]))

            # Average percent difference
            avg_diff = sum(abs(r['percent_difference']) for r in all_comparisons
                          if r['percent_difference'] is not None) / compared_count

            logger.info(f"\n{'='*70}")
            logger.info(f"Correlation Analysis")
            logger.info(f"{'='*70}")
            logger.info(f"Journals compared: {compared_count}/{len(journals)}")
            logger.info(f"")
            logger.info(f"Correlation Metrics:")
            logger.info(f"  Pearson correlation:  r = {pearson_r:.4f} (p = {pearson_p:.4e})")
            logger.info(f"  Spearman correlation: ρ = {spearman_r:.4f} (p = {spearman_p:.4e})")
            logger.info(f"")
            logger.info(f"Error Metrics:")
            logger.info(f"  Mean Absolute Error (MAE):  {mae:.3f}")
            logger.info(f"  Root Mean Square Error (RMSE): {rmse:.3f}")
            logger.info(f"  Average Percent Difference: {avg_diff:.1f}%")
            logger.info(f"")

            # Interpretation
            if pearson_r > 0.95:
                logger.info(f"Interpretation: Excellent agreement (r > 0.95)")
            elif pearson_r > 0.90:
                logger.info(f"Interpretation: Very strong agreement (r > 0.90)")
            elif pearson_r > 0.80:
                logger.info(f"Interpretation: Strong agreement (r > 0.80)")
            elif pearson_r > 0.70:
                logger.info(f"Interpretation: Moderate agreement (r > 0.70)")
            else:
                logger.info(f"Interpretation: Weak agreement (r < 0.70)")

            logger.info(f"{'='*70}")

            # Save correlation data if output specified
            if args.output:
                corr_output = args.output.replace('.csv', '_correlation.txt')
                with open(corr_output, 'w') as f:
                    f.write(f"Correlation Analysis Results\n")
                    f.write(f"="*70 + "\n\n")
                    f.write(f"Journals compared: {compared_count}\n\n")
                    f.write(f"Correlation Metrics:\n")
                    f.write(f"  Pearson correlation:  r = {pearson_r:.4f} (p = {pearson_p:.4e})\n")
                    f.write(f"  Spearman correlation: ρ = {spearman_r:.4f} (p = {spearman_p:.4e})\n\n")
                    f.write(f"Error Metrics:\n")
                    f.write(f"  Mean Absolute Error (MAE):  {mae:.3f}\n")
                    f.write(f"  Root Mean Square Error (RMSE): {rmse:.3f}\n")
                    f.write(f"  Average Percent Difference: {avg_diff:.1f}%\n\n")
                    f.write(f"Data pairs (Calculated, JCR):\n")
                    for calc, jcr in zip(calc_ifs, jcr_ifs):
                        f.write(f"  {calc:.3f}, {jcr:.3f}\n")

                logger.info(f"Correlation analysis saved to: {corr_output}")
        else:
            avg_diff = sum(abs(r['percent_difference']) for r in all_comparisons
                          if r['percent_difference'] is not None) / compared_count
            logger.info(f"\n{'='*70}")
            logger.info(f"Summary: {compared_count}/{len(journals)} journals compared")
            logger.info(f"Average absolute percent difference: {avg_diff:.1f}%")
            logger.info(f"Note: Need at least 3 journals for correlation analysis")
            logger.info(f"{'='*70}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

# EOF
