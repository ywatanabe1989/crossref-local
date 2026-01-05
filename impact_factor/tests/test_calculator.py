#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick test script for impact factor calculator.

Tests basic functionality without requiring full calculations.
"""

import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test database connection and basic queries."""
    from calculator import ImpactFactorCalculator

    logger.info("Testing database connection...")

    try:
        calc = ImpactFactorCalculator()
        logger.info("✓ Database connection successful")

        # Test ISSN lookup
        issn = calc.get_journal_issn("Nature")
        logger.info(f"✓ ISSN lookup: Nature -> {issn}")

        # Test article count
        count = calc.count_articles("Nature", 2023)
        logger.info(f"✓ Article count: Nature (2023) -> {count} articles")

        calc.close()
        return True

    except Exception as e:
        logger.error(f"✗ Database test failed: {e}")
        return False


def test_calculation():
    """Test impact factor calculation."""
    from calculator import ImpactFactorCalculator

    logger.info("\nTesting impact factor calculation...")

    try:
        with ImpactFactorCalculator() as calc:
            # Calculate IF for Nature 2023 (should be fast with is-referenced-by method)
            result = calc.calculate_impact_factor(
                journal_identifier="Nature",
                target_year=2023,
                window_years=2,
                method="is-referenced-by"
            )

            logger.info(f"✓ Calculation successful:")
            logger.info(f"  Journal: {result['journal']}")
            logger.info(f"  Year: {result['target_year']}")
            logger.info(f"  Articles: {result['total_articles']}")
            logger.info(f"  Citations: {result['total_citations']}")
            logger.info(f"  Impact Factor: {result['impact_factor']:.3f}")

            if result['total_articles'] == 0:
                logger.warning("  ⚠ No articles found - check journal name or year")
                return False

            return True

    except Exception as e:
        logger.error(f"✗ Calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_time_series():
    """Test time series calculation."""
    from calculator import ImpactFactorCalculator

    logger.info("\nTesting time series calculation...")

    try:
        with ImpactFactorCalculator() as calc:
            # Calculate IF for 3 years
            results = calc.calculate_if_time_series(
                journal_identifier="Nature",
                start_year=2021,
                end_year=2023,
                window_years=2
            )

            logger.info(f"✓ Time series calculation successful:")
            for result in results:
                logger.info(f"  {result['target_year']}: IF = {result['impact_factor']:.3f}")

            return True

    except Exception as e:
        logger.error(f"✗ Time series test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("="*70)
    logger.info("Impact Factor Calculator - Test Suite")
    logger.info("="*70)

    tests = [
        ("Database Connection", test_database_connection),
        ("Basic Calculation", test_calculation),
        ("Time Series", test_time_series),
    ]

    results = []
    for test_name, test_func in tests:
        logger.info(f"\n{'='*70}")
        logger.info(f"Running: {test_name}")
        logger.info(f"{'='*70}")

        passed = test_func()
        results.append((test_name, passed))

    # Summary
    logger.info(f"\n{'='*70}")
    logger.info("Test Summary")
    logger.info(f"{'='*70}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        logger.info("\n🎉 All tests passed!")
        return 0
    else:
        logger.error(f"\n❌ {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# EOF
