#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-02-10 (ywatanabe)"
# File: /home/ywatanabe/proj/crossref-local/examples/11_abstract_coverage.py

"""Calculate abstract coverage statistics for Crossref Local database.

This script calculates:
1. Global abstract availability ratio
2. Per-type coverage (journal-article, book-chapter, etc.)
3. Per-publisher coverage (by member ID)
4. Per-year coverage
"""

import json
import sqlite3
from pathlib import Path

import scitex as stx

# Database path
DB_PATH = Path.home() / "proj" / "crossref-local" / "data" / "crossref.db"


def get_connection():
    """Get database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@stx.session
def main(
    top_n: int = 20,
    CONFIG=stx.session.INJECTED,
    plt=stx.session.INJECTED,
    logger=stx.session.INJECTED,
):
    """Calculate abstract coverage statistics.

    Args:
        top_n: Number of top publishers to show
    """
    conn = get_connection()
    cursor = conn.cursor()

    # =========================================================================
    # 1. Global Coverage
    # =========================================================================
    logger.info("=" * 70)
    logger.info("ABSTRACT COVERAGE STATISTICS (Crossref)")
    logger.info("=" * 70)

    # Count total and those with abstract in metadata JSON
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN json_extract(metadata, '$.abstract') IS NOT NULL
                      AND json_extract(metadata, '$.abstract') != '' THEN 1 ELSE 0 END) as with_abstract
        FROM works
    """)
    result = cursor.fetchone()

    total = result['total']
    with_abstract = result['with_abstract']
    ratio = (with_abstract / total) * 100

    logger.info(f"\nGlobal Statistics:")
    logger.info(f"  Total works: {total:,}")
    logger.info(f"  With abstract: {with_abstract:,}")
    logger.info(f"  Coverage: {ratio:.1f}%")

    # =========================================================================
    # 1b. Coverage by Work Type
    # =========================================================================
    logger.info("\n" + "-" * 70)
    logger.info("Coverage by Work Type")
    logger.info("-" * 70)
    logger.info("(Note: book-review, editorial, letter, etc. often lack abstracts by design)")

    cursor.execute("""
        SELECT
            type,
            COUNT(*) as total,
            SUM(CASE WHEN json_extract(metadata, '$.abstract') IS NOT NULL
                      AND json_extract(metadata, '$.abstract') != '' THEN 1 ELSE 0 END) as with_abstract
        FROM works
        WHERE type IS NOT NULL AND type != ''
        GROUP BY type
        ORDER BY total DESC
        LIMIT 25
    """)
    types = cursor.fetchall()

    logger.info(f"\n{'Work Type':<35} {'Total':>15} {'Abstract':>15} {'Coverage':>10}")
    logger.info("-" * 77)
    for row in types:
        coverage = (row['with_abstract'] / row['total']) * 100 if row['total'] > 0 else 0
        logger.info(f"{row['type']:<35} {row['total']:>15,} {row['with_abstract']:>15,} {coverage:>9.1f}%")

    # Highlight journal-article specifically
    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN json_extract(metadata, '$.abstract') IS NOT NULL
                      AND json_extract(metadata, '$.abstract') != '' THEN 1 ELSE 0 END) as with_abstract
        FROM works
        WHERE type = 'journal-article'
    """)
    journal_article = cursor.fetchone()
    if journal_article and journal_article['total'] > 0:
        ja_coverage = (journal_article['with_abstract'] / journal_article['total']) * 100
        logger.info(f"\n>>> Journal-article coverage: {ja_coverage:.1f}% ({journal_article['with_abstract']:,} / {journal_article['total']:,})")

    # =========================================================================
    # 2. Per-Member/Publisher Coverage (Top N)
    # =========================================================================
    logger.info("\n" + "-" * 70)
    logger.info(f"Coverage by Publisher/Member (Top {top_n})")
    logger.info("-" * 70)

    cursor.execute(f"""
        SELECT
            member,
            COUNT(*) as total,
            SUM(CASE WHEN json_extract(metadata, '$.abstract') IS NOT NULL
                      AND json_extract(metadata, '$.abstract') != '' THEN 1 ELSE 0 END) as with_abstract
        FROM works
        WHERE member IS NOT NULL
        GROUP BY member
        HAVING total > 10000
        ORDER BY total DESC
        LIMIT {top_n}
    """)
    members = cursor.fetchall()

    logger.info(f"\n{'Member ID':<15} {'Total':>15} {'Abstract':>15} {'Coverage':>10}")
    logger.info("-" * 57)
    for row in members:
        coverage = (row['with_abstract'] / row['total']) * 100 if row['total'] > 0 else 0
        logger.info(f"{row['member']:<15} {row['total']:>15,} {row['with_abstract']:>15,} {coverage:>9.1f}%")

    # =========================================================================
    # 3. Coverage by Year
    # =========================================================================
    logger.info("\n" + "-" * 70)
    logger.info("Coverage by Publication Year (Recent 10 Years)")
    logger.info("-" * 70)

    cursor.execute("""
        SELECT
            CAST(strftime('%Y', created_date_time) AS INTEGER) as year,
            COUNT(*) as total,
            SUM(CASE WHEN json_extract(metadata, '$.abstract') IS NOT NULL
                      AND json_extract(metadata, '$.abstract') != '' THEN 1 ELSE 0 END) as with_abstract
        FROM works
        WHERE created_date_time IS NOT NULL
          AND CAST(strftime('%Y', created_date_time) AS INTEGER) >= 2014
          AND CAST(strftime('%Y', created_date_time) AS INTEGER) <= 2024
        GROUP BY year
        ORDER BY year DESC
    """)
    years = cursor.fetchall()

    logger.info(f"\n{'Year':<10} {'Total':>15} {'Abstract':>15} {'Coverage':>10}")
    logger.info("-" * 52)
    for row in years:
        coverage = (row['with_abstract'] / row['total']) * 100 if row['total'] > 0 else 0
        logger.info(f"{row['year']:<10} {row['total']:>15,} {row['with_abstract']:>15,} {coverage:>9.1f}%")

    # =========================================================================
    # 4. Summary
    # =========================================================================
    logger.info("\n" + "=" * 70)
    logger.info("SUMMARY (for documentation)")
    logger.info("=" * 70)
    logger.info(f"\nGlobal abstract coverage: {ratio:.1f}%")
    logger.info(f"Total indexed works: {total:,}")

    # Save summary to CSV
    import pandas as pd

    # Type coverage
    type_data = [{"type": row['type'], "total": row['total'], "with_abstract": row['with_abstract'],
                  "coverage": round((row['with_abstract'] / row['total']) * 100, 1) if row['total'] > 0 else 0}
                 for row in types]
    df_type = pd.DataFrame(type_data)
    stx.io.save(df_type, "type_coverage.csv")

    # Year coverage
    year_data = [{"year": row['year'], "total": row['total'], "with_abstract": row['with_abstract'],
                  "coverage": round((row['with_abstract'] / row['total']) * 100, 1) if row['total'] > 0 else 0}
                 for row in years]
    df_year = pd.DataFrame(year_data)
    stx.io.save(df_year, "year_coverage.csv")

    logger.info("\nSaved: type_coverage.csv, year_coverage.csv")

    conn.close()
    return 0


if __name__ == "__main__":
    main()

# EOF
