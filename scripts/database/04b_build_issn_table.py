#!/usr/bin/env python3
"""
Build ISSN-based journal lookup table (ISSN-first approach).

This is faster than GROUP BY on journal names because:
1. ISSN is already indexed in works table
2. We iterate over unique ISSNs and sample journal names
3. For non-1:1 mappings, we take the most common name (statistical)

Usage:
    python build_issn_table.py --db /path/to/crossref.db
"""

import argparse
import logging
import sqlite3
import time
from pathlib import Path
from collections import Counter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def build_issn_table(db_path: str, batch_size: int = 10000) -> None:
    """
    Build ISSN-based journal lookup table.

    Args:
        db_path: Path to CrossRef SQLite database
        batch_size: Number of ISSNs to process per batch
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Set temp directory
    db_dir = str(Path(db_path).parent.resolve())
    cursor.execute(f"PRAGMA temp_store_directory = '{db_dir}'")
    logger.info(f"SQLite temp directory set to: {db_dir}")

    logger.info("Building ISSN-based journal lookup table...")
    start_time = time.time()

    # Drop existing table
    cursor.execute("DROP TABLE IF EXISTS journals")
    conn.commit()

    # Create new table with ISSN as primary lookup
    logger.info("Creating journals table (ISSN-first schema)...")
    cursor.execute("""
        CREATE TABLE journals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issn TEXT UNIQUE NOT NULL,
            issn_alt TEXT,
            name TEXT,
            name_lower TEXT,
            publisher TEXT,
            article_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()

    # Step 1: Get unique ISSNs using the index
    logger.info("Step 1: Extracting unique ISSNs (using idx_issn)...")
    cursor.execute("""
        SELECT DISTINCT json_extract(metadata, '$.ISSN[0]') as issn
        FROM works
        WHERE type = 'journal-article'
        AND json_extract(metadata, '$.ISSN[0]') IS NOT NULL
    """)

    all_issns = [row[0] for row in cursor.fetchall()]
    total_issns = len(all_issns)
    logger.info(f"Found {total_issns:,} unique ISSNs")

    # Step 2: For each ISSN, get journal info (statistically most common name)
    logger.info("Step 2: Resolving journal names for each ISSN...")

    inserted = 0
    for i in range(0, total_issns, batch_size):
        batch = all_issns[i:i + batch_size]
        batch_data = []

        for issn in batch:
            # Get all names and count for this ISSN
            cursor.execute("""
                SELECT
                    json_extract(metadata, '$.container-title[0]') as name,
                    json_extract(metadata, '$.ISSN[1]') as issn_alt,
                    json_extract(metadata, '$.publisher') as publisher,
                    COUNT(*) as cnt
                FROM works
                WHERE json_extract(metadata, '$.ISSN[0]') = ?
                AND type = 'journal-article'
                GROUP BY json_extract(metadata, '$.container-title[0]')
                ORDER BY cnt DESC
                LIMIT 1
            """, (issn,))

            row = cursor.fetchone()
            if row and row[0]:  # has name
                name, issn_alt, publisher, article_count = row
                batch_data.append((
                    issn,
                    issn_alt,
                    name,
                    name.lower() if name else None,
                    publisher,
                    article_count
                ))

        # Batch insert
        cursor.executemany("""
            INSERT OR IGNORE INTO journals
            (issn, issn_alt, name, name_lower, publisher, article_count)
            VALUES (?, ?, ?, ?, ?, ?)
        """, batch_data)
        conn.commit()

        inserted += len(batch_data)
        elapsed = time.time() - start_time
        rate = inserted / elapsed if elapsed > 0 else 0
        eta = (total_issns - i - batch_size) / rate / 60 if rate > 0 else 0

        logger.info(
            f"Progress: {i + len(batch):,}/{total_issns:,} ISSNs "
            f"({inserted:,} inserted, {rate:.1f}/s, ETA: {eta:.1f}m)"
        )

    # Create indexes
    logger.info("Creating indexes...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_journals_issn ON journals(issn)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_journals_name_lower ON journals(name_lower)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_journals_name ON journals(name)")
    conn.commit()

    # Final stats
    cursor.execute("SELECT COUNT(*) FROM journals")
    final_count = cursor.fetchone()[0]

    elapsed = time.time() - start_time
    logger.info(f"Done! Built table with {final_count:,} journals in {elapsed/60:.1f} minutes")

    # Show top journals
    logger.info("Top 10 journals by article count:")
    cursor.execute("""
        SELECT name, issn, article_count
        FROM journals
        ORDER BY article_count DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        logger.info(f"  {row[0][:50]:<50} {row[1]:<12} {row[2]:>8,}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Build ISSN-based journal lookup table")
    parser.add_argument("--db", default="./data/crossref.db")
    parser.add_argument("--batch-size", type=int, default=10000)
    args = parser.parse_args()

    if not Path(args.db).exists():
        logger.error(f"Database not found: {args.db}")
        return 1

    build_issn_table(args.db, args.batch_size)
    return 0


if __name__ == "__main__":
    exit(main())
