#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-14"
# Author: ywatanabe (with Claude)
# File: 06_calculate_abstract_ratio.py

"""
Calculate the ratio of works with abstracts in the CrossRef database.

Uses sampling for fast estimation or full scan for exact count.

Usage:
    python 06_calculate_abstract_ratio.py [--full] [--sample-size N]
"""

import argparse
import random
import sqlite3
import sys
import time
import zlib
import json
from pathlib import Path

DEFAULT_DB_PATH = "./data/crossref.db"


def decompress_metadata(data: bytes) -> dict:
    """Decompress metadata from database."""
    if data is None:
        return {}
    try:
        if data[:2] == b'x\x9c' or data[:2] == b'x\xda':
            decompressed = zlib.decompress(data)
            return json.loads(decompressed)
        return json.loads(data)
    except Exception:
        return {}


def sample_estimate(conn: sqlite3.Connection, sample_size: int = 10000) -> dict:
    """Estimate abstract ratio using random sampling."""
    print(f"Sampling {sample_size:,} works for quick estimate...")
    start = time.time()

    # Get max rowid
    cursor = conn.execute("SELECT COUNT(*) as total, MAX(rowid) as max_id FROM works")
    row = cursor.fetchone()
    total = row[0]
    max_id = row[1]

    # Random sample
    random.seed(42)  # Reproducible
    sample_ids = random.sample(range(1, max_id + 1), min(sample_size * 2, max_id))

    has_abstract = 0
    checked = 0

    for rid in sample_ids:
        if checked >= sample_size:
            break
        cursor = conn.execute("SELECT metadata FROM works WHERE rowid = ?", (rid,))
        row = cursor.fetchone()
        if row:
            meta = decompress_metadata(row[0])
            if meta.get("abstract"):
                has_abstract += 1
            checked += 1

    elapsed = time.time() - start
    ratio = has_abstract / checked if checked > 0 else 0

    return {
        "method": "sample",
        "sample_size": checked,
        "with_abstract": has_abstract,
        "ratio": ratio,
        "estimated_total_with_abstract": int(total * ratio),
        "total_works": total,
        "elapsed_seconds": elapsed,
    }


def full_count(conn: sqlite3.Connection) -> dict:
    """Full count of works with abstracts (slow)."""
    print("Counting all works with abstracts (this may take hours)...")
    start = time.time()

    cursor = conn.execute("SELECT COUNT(*) as total FROM works")
    total = cursor.fetchone()[0]

    cursor = conn.execute("""
        SELECT COUNT(*) as c FROM works
        WHERE json_extract(metadata, '$.abstract') IS NOT NULL
        AND json_extract(metadata, '$.abstract') != ''
    """)
    with_abstract = cursor.fetchone()[0]

    elapsed = time.time() - start
    ratio = with_abstract / total if total > 0 else 0

    return {
        "method": "full",
        "with_abstract": with_abstract,
        "ratio": ratio,
        "total_works": total,
        "elapsed_seconds": elapsed,
    }


def main():
    parser = argparse.ArgumentParser(description="Calculate abstract availability ratio")
    parser.add_argument(
        "--db-path",
        type=str,
        default=DEFAULT_DB_PATH,
        help=f"Path to SQLite database (default: {DEFAULT_DB_PATH})",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Do full count instead of sampling (very slow)",
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=10000,
        help="Sample size for estimation (default: 10000)",
    )
    args = parser.parse_args()

    db_path = Path(args.db_path)
    if not db_path.exists():
        print(f"Database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Opening database: {db_path}")
    conn = sqlite3.connect(str(db_path), timeout=300)

    try:
        if args.full:
            result = full_count(conn)
        else:
            result = sample_estimate(conn, args.sample_size)

        print()
        print("=" * 50)
        print("Abstract Availability Report")
        print("=" * 50)
        print(f"Method: {result['method']}")
        print(f"Total works: {result['total_works']:,}")
        if result['method'] == 'sample':
            print(f"Sample size: {result['sample_size']:,}")
            print(f"With abstract (sample): {result['with_abstract']:,}")
            print(f"Estimated total with abstract: {result['estimated_total_with_abstract']:,}")
        else:
            print(f"With abstract: {result['with_abstract']:,}")
        print(f"Ratio: {result['ratio']:.1%}")
        print(f"Elapsed: {result['elapsed_seconds']:.1f}s")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
