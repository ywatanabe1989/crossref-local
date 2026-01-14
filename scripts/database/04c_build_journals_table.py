#!/usr/bin/env python3
"""
Build journals lookup table for fast name-to-ISSN resolution.

This script creates an indexed lookup table mapping journal names to ISSNs,
enabling fast journal identification without scanning the full works table.

Usage:
    python build_journals_table.py --db /path/to/crossref.db
    python build_journals_table.py --db /path/to/crossref.db --batch-size 100000
"""

import argparse
import logging
import sqlite3
import time
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def build_journals_table(db_path: str, batch_size: int = 50000) -> None:
    """
    Build journals lookup table from works table.

    Args:
        db_path: Path to CrossRef SQLite database
        batch_size: Number of rows to process per batch
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Set temp directory to database directory (avoids /tmp space issues)
    db_dir = str(Path(db_path).parent.resolve())
    cursor.execute(f"PRAGMA temp_store_directory = '{db_dir}'")
    logger.info(f"SQLite temp directory set to: {db_dir}")

    logger.info("Building journals lookup table...")
    start_time = time.time()

    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='journals'
    """)
    if cursor.fetchone():
        logger.info("Dropping existing journals table...")
        cursor.execute("DROP TABLE journals")
        conn.commit()

    # Create journals table with unique constraint
    logger.info("Creating journals table...")
    cursor.execute("""
        CREATE TABLE journals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            name_lower TEXT NOT NULL,
            issn TEXT,
            issn_alt TEXT,
            publisher TEXT,
            article_count INTEGER DEFAULT 0,
            UNIQUE(name, issn)
        )
    """)
    conn.commit()

    # Count total works for progress
    cursor.execute("SELECT COUNT(*) FROM works WHERE type = 'journal-article'")
    total_works = cursor.fetchone()[0]
    logger.info(f"Processing {total_works:,} journal articles...")

    # Extract unique journal/ISSN combinations
    logger.info("Extracting unique journals (this may take a while)...")

    cursor.execute("""
        INSERT OR IGNORE INTO journals (name, name_lower, issn, issn_alt, publisher, article_count)
        SELECT
            json_extract(metadata, '$.container-title[0]') as name,
            LOWER(json_extract(metadata, '$.container-title[0]')) as name_lower,
            json_extract(metadata, '$.ISSN[0]') as issn,
            json_extract(metadata, '$.ISSN[1]') as issn_alt,
            json_extract(metadata, '$.publisher') as publisher,
            COUNT(*) as article_count
        FROM works
        WHERE type = 'journal-article'
        AND json_extract(metadata, '$.container-title[0]') IS NOT NULL
        GROUP BY
            json_extract(metadata, '$.container-title[0]'),
            json_extract(metadata, '$.ISSN[0]')
    """)
    conn.commit()

    # Get count of journals
    cursor.execute("SELECT COUNT(*) FROM journals")
    journal_count = cursor.fetchone()[0]
    logger.info(f"Extracted {journal_count:,} unique journals")

    # Create indexes
    logger.info("Creating indexes...")

    cursor.execute("CREATE INDEX idx_journals_name ON journals(name)")
    cursor.execute("CREATE INDEX idx_journals_name_lower ON journals(name_lower)")
    cursor.execute("CREATE INDEX idx_journals_issn ON journals(issn)")
    conn.commit()

    elapsed = time.time() - start_time
    logger.info(f"Journals table built in {elapsed/60:.1f} minutes")

    # Show sample
    logger.info("Sample entries:")
    cursor.execute("""
        SELECT name, issn, article_count
        FROM journals
        ORDER BY article_count DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        logger.info(f"  {row[0][:40]:<40} {row[1] or 'N/A':<12} {row[2]:>8,} articles")

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Build journals lookup table"
    )
    parser.add_argument(
        "--db",
        default="./data/crossref.db",
        help="Path to CrossRef database"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50000,
        help="Batch size for processing"
    )
    args = parser.parse_args()

    if not Path(args.db).exists():
        logger.error(f"Database not found: {args.db}")
        return 1

    build_journals_table(args.db, args.batch_size)
    return 0


if __name__ == "__main__":
    exit(main())
