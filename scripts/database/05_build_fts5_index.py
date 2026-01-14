#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-07"
# Author: ywatanabe (with Claude)
# File: build_fts5_index.py

"""
Build FTS5 full-text search index for CrossRef database.

Indexes title, abstract, and authors for fast text search.
Expected runtime: Several hours for 167M+ records.

Usage:
    python build_fts5_index.py [--db-path PATH] [--batch-size N]
"""

import argparse
import json
import logging
import sqlite3
import sys
import time
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("build_fts5_index.log"),
    ],
)
logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = "./data/crossref.db"
BATCH_SIZE = 50000


def flatten_authors(authors_json: str) -> str:
    """Flatten authors JSON array to searchable string."""
    if not authors_json:
        return ""
    try:
        authors = json.loads(authors_json)
        if not isinstance(authors, list):
            return ""
        names = []
        for author in authors:
            if isinstance(author, dict):
                given = author.get("given", "")
                family = author.get("family", "")
                if given or family:
                    names.append(f"{given} {family}".strip())
        return " | ".join(names)
    except (json.JSONDecodeError, TypeError):
        return ""


def create_fts5_table(conn: sqlite3.Connection) -> None:
    """Create FTS5 virtual table if not exists."""
    logger.info("Creating FTS5 virtual table...")

    # Drop existing table if rebuilding
    conn.execute("DROP TABLE IF EXISTS works_fts")

    # Create FTS5 table with content sync
    conn.execute("""
        CREATE VIRTUAL TABLE works_fts USING fts5(
            doi,
            title,
            abstract,
            authors,
            content='',
            tokenize='porter unicode61'
        )
    """)
    conn.commit()
    logger.info("FTS5 table created successfully")


def get_total_count(conn: sqlite3.Connection) -> int:
    """Get total number of records in works table."""
    cursor = conn.execute("SELECT COUNT(*) FROM works")
    return cursor.fetchone()[0]


def populate_fts5_table(conn: sqlite3.Connection, batch_size: int = BATCH_SIZE) -> None:
    """Populate FTS5 table from works table."""

    # Register the flatten_authors function
    conn.create_function("flatten_authors", 1, flatten_authors)

    total = get_total_count(conn)
    logger.info(f"Total records to index: {total:,}")

    processed = 0
    start_time = time.time()
    last_log_time = start_time

    # Use cursor to iterate through all records
    cursor = conn.execute("""
        SELECT
            id,
            doi,
            json_extract(metadata, '$.title[0]') as title,
            json_extract(metadata, '$.abstract') as abstract,
            json_extract(metadata, '$.author') as authors_json
        FROM works
    """)

    batch = []
    for row in cursor:
        work_id, doi, title, abstract, authors_json = row

        # Flatten authors
        authors = flatten_authors(authors_json)

        # Clean up values
        doi = doi or ""
        title = title or ""
        abstract = abstract or ""

        batch.append((doi, title, abstract, authors))

        if len(batch) >= batch_size:
            # Insert batch
            conn.executemany(
                "INSERT INTO works_fts(doi, title, abstract, authors) VALUES (?, ?, ?, ?)",
                batch
            )
            conn.commit()
            processed += len(batch)
            batch = []

            # Log progress
            current_time = time.time()
            if current_time - last_log_time >= 30:  # Log every 30 seconds
                elapsed = current_time - start_time
                rate = processed / elapsed
                eta = (total - processed) / rate if rate > 0 else 0
                progress = (processed / total) * 100
                logger.info(
                    f"Progress: {processed:,}/{total:,} ({progress:.1f}%) | "
                    f"Rate: {rate:.0f} rec/s | ETA: {eta/3600:.1f}h"
                )
                last_log_time = current_time

    # Insert remaining batch
    if batch:
        conn.executemany(
            "INSERT INTO works_fts(doi, title, abstract, authors) VALUES (?, ?, ?, ?)",
            batch
        )
        conn.commit()
        processed += len(batch)

    elapsed = time.time() - start_time
    logger.info(f"Indexing complete: {processed:,} records in {elapsed/3600:.2f} hours")


def verify_fts5(conn: sqlite3.Connection) -> None:
    """Run verification queries on FTS5 table."""
    logger.info("Verifying FTS5 index...")

    # Count records
    cursor = conn.execute("SELECT COUNT(*) FROM works_fts")
    count = cursor.fetchone()[0]
    logger.info(f"FTS5 table contains {count:,} records")

    # Test search
    test_queries = ["hippocampus", "machine learning", "COVID-19"]
    for query in test_queries:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM works_fts WHERE works_fts MATCH ?",
            (query,)
        )
        match_count = cursor.fetchone()[0]
        logger.info(f"Test query '{query}': {match_count:,} matches")


def main():
    parser = argparse.ArgumentParser(description="Build FTS5 index for CrossRef database")
    parser.add_argument(
        "--db-path",
        type=str,
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Batch size for inserts (default: {BATCH_SIZE})",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify existing FTS5 index",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path)
    if not db_path.exists():
        logger.error(f"Database not found: {db_path}")
        sys.exit(1)

    logger.info(f"Opening database: {db_path}")
    conn = sqlite3.connect(str(db_path), timeout=300)

    # Enable WAL mode for better concurrent access
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-2000000")  # 2GB cache

    try:
        if args.verify_only:
            verify_fts5(conn)
        else:
            create_fts5_table(conn)
            populate_fts5_table(conn, args.batch_size)
            verify_fts5(conn)
    finally:
        conn.close()

    logger.info("Done!")


if __name__ == "__main__":
    main()
