#!/usr/bin/env python3
"""
Build journal mapping from ISSN list using CrossRef database.

Uses issnlister's 2.44M ISSNs as input, queries CrossRef for journal names.
Much faster than GROUP BY since we use the idx_issn index directly.

Usage:
    python build_from_issn_list.py --db /path/to/crossref.db --issn-file issn.tsv
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


def build_from_issn_list(db_path: str, issn_file: str, batch_size: int = 1000) -> None:
    """Build journal table from ISSN list."""

    # Load ISSNs
    logger.info(f"Loading ISSNs from {issn_file}...")
    with open(issn_file) as f:
        all_issns = [line.strip() for line in f if line.strip()]
    logger.info(f"Loaded {len(all_issns):,} ISSNs")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Set temp directory
    db_dir = str(Path(db_path).parent.resolve())
    cursor.execute(f"PRAGMA temp_store_directory = '{db_dir}'")

    # Create table
    logger.info("Creating journals_crossref table...")
    cursor.execute("DROP TABLE IF EXISTS journals_crossref")
    cursor.execute("""
        CREATE TABLE journals_crossref (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issn TEXT UNIQUE NOT NULL,
            issn_alt TEXT,
            name TEXT,
            name_lower TEXT,
            short_name TEXT,
            publisher TEXT,
            article_count INTEGER DEFAULT 0
        )
    """)
    conn.commit()

    start_time = time.time()
    found = 0
    not_found = 0

    # Process in batches
    for i in range(0, len(all_issns), batch_size):
        batch = all_issns[i:i + batch_size]
        batch_data = []

        for issn in batch:
            # Fast query: just get one sample record (uses idx_issn index)
            cursor.execute("""
                SELECT
                    json_extract(metadata, '$.container-title[0]') as name,
                    json_extract(metadata, '$.short-container-title[0]') as short_name,
                    json_extract(metadata, '$.ISSN[1]') as issn_alt,
                    json_extract(metadata, '$.publisher') as publisher
                FROM works
                WHERE json_extract(metadata, '$.ISSN[0]') = ?
                AND type = 'journal-article'
                LIMIT 1
            """, (issn,))

            row = cursor.fetchone()
            if row and row[0]:  # has name
                name, short_name, issn_alt, publisher = row
                batch_data.append((
                    issn,
                    issn_alt,
                    name,
                    name.lower() if name else None,
                    short_name,
                    publisher,
                    0  # article_count computed later
                ))
                found += 1
            else:
                not_found += 1

        # Batch insert
        if batch_data:
            cursor.executemany("""
                INSERT OR IGNORE INTO journals_crossref
                (issn, issn_alt, name, name_lower, short_name, publisher, article_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, batch_data)
            conn.commit()

        # Progress
        processed = i + len(batch)
        elapsed = time.time() - start_time
        rate = processed / elapsed if elapsed > 0 else 0
        eta = (len(all_issns) - processed) / rate / 60 if rate > 0 else 0

        if (i // batch_size) % 100 == 0:  # Log every 100 batches
            logger.info(
                f"Progress: {processed:,}/{len(all_issns):,} ISSNs "
                f"({found:,} found, {not_found:,} not in CrossRef, "
                f"{rate:.1f}/s, ETA: {eta:.1f}m)"
            )

    # Create indexes
    logger.info("Creating indexes...")
    cursor.execute("CREATE INDEX idx_jcr_issn ON journals_crossref(issn)")
    cursor.execute("CREATE INDEX idx_jcr_name_lower ON journals_crossref(name_lower)")
    cursor.execute("CREATE INDEX idx_jcr_name ON journals_crossref(name)")
    conn.commit()

    # Final stats
    cursor.execute("SELECT COUNT(*) FROM journals_crossref")
    final_count = cursor.fetchone()[0]

    elapsed = time.time() - start_time
    logger.info(f"\nDone! Built table with {final_count:,} journals in {elapsed/60:.1f} minutes")
    logger.info(f"Found in CrossRef: {found:,}")
    logger.info(f"Not found: {not_found:,}")

    # Show top journals
    logger.info("\nTop 10 journals by article count:")
    cursor.execute("""
        SELECT name, issn, article_count
        FROM journals_crossref
        ORDER BY article_count DESC
        LIMIT 10
    """)
    for row in cursor.fetchall():
        logger.info(f"  {row[0][:50]:<50} {row[1]:<12} {row[2]:>10,}")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Build journal table from ISSN list")
    parser.add_argument("--db", default="./data/crossref.db")
    parser.add_argument("--issn-file", default="./data/external/issn.tsv")
    parser.add_argument("--batch-size", type=int, default=1000)
    args = parser.parse_args()

    if not Path(args.db).exists():
        logger.error(f"Database not found: {args.db}")
        return 1

    if not Path(args.issn_file).exists():
        logger.error(f"ISSN file not found: {args.issn_file}")
        return 1

    build_from_issn_list(args.db, args.issn_file, args.batch_size)
    return 0


if __name__ == "__main__":
    exit(main())
