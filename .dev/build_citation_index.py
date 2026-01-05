#!/usr/bin/env python3
"""
Build a citation index table for fast IF calculations.
This is a one-time preprocessing step that extracts all citation relationships.

This creates a table: citations(citing_doi, cited_doi, citing_year)
Which enables fast lookup of citations by year.
"""

import sqlite3
import json
import time
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "../data/crossref.db"

def build_citation_index(year=2023, batch_size=10000):
    """
    Build citation index for a specific year.
    This extracts all citation relationships from articles published in that year.
    """

    print("="*60)
    print(f"Building Citation Index for {year}")
    print("="*60)
    print(f"Database: {DB_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)

    # Create citations table if it doesn't exist
    print("Creating citations table...")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS citations (
            citing_doi TEXT,
            cited_doi TEXT,
            citing_year INTEGER,
            PRIMARY KEY (citing_doi, cited_doi)
        )
    """)

    # Create indexes for fast lookup
    conn.execute("CREATE INDEX IF NOT EXISTS idx_citations_cited ON citations(cited_doi, citing_year)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_citations_year ON citations(citing_year)")
    conn.commit()
    print("✓ Table and indexes created")
    print()

    # Count articles to process
    print(f"Counting articles in {year}...")
    cursor = conn.execute("""
        SELECT COUNT(*)
        FROM works
        WHERE json_extract(metadata, '$.published.date-parts[0][0]') = ?
        AND json_extract(metadata, '$.reference') IS NOT NULL
    """, (year,))

    total_articles = cursor.fetchone()[0]
    print(f"Found {total_articles:,} articles with references")
    print()

    # Check if already processed
    cursor = conn.execute("SELECT COUNT(*) FROM citations WHERE citing_year = ?", (year,))
    existing = cursor.fetchone()[0]

    if existing > 0:
        print(f"⚠️  Found {existing:,} existing citations for {year}")
        response = input("Delete and rebuild? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled")
            return

        print(f"Deleting existing {year} citations...")
        conn.execute("DELETE FROM citations WHERE citing_year = ?", (year,))
        conn.commit()
        print("✓ Deleted")
        print()

    # Process articles in batches
    print(f"Processing articles (batch size: {batch_size:,})...")
    print("-"*60)

    offset = 0
    total_citations = 0
    start_time = time.time()

    while offset < total_articles:
        batch_start = time.time()

        # Fetch batch
        cursor = conn.execute("""
            SELECT doi, metadata
            FROM works
            WHERE json_extract(metadata, '$.published.date-parts[0][0]') = ?
            AND json_extract(metadata, '$.reference') IS NOT NULL
            LIMIT ? OFFSET ?
        """, (year, batch_size, offset))

        # Extract citations
        citations_batch = []
        for row in cursor:
            citing_doi = row[0]
            metadata = json.loads(row[1])
            references = metadata.get('reference', [])

            for ref in references:
                cited_doi = ref.get('DOI')
                if cited_doi:
                    citations_batch.append((citing_doi, cited_doi.lower(), year))

        # Insert batch
        if citations_batch:
            conn.executemany(
                "INSERT OR IGNORE INTO citations (citing_doi, cited_doi, citing_year) VALUES (?, ?, ?)",
                citations_batch
            )
            conn.commit()
            total_citations += len(citations_batch)

        offset += batch_size
        batch_time = time.time() - batch_start
        elapsed = time.time() - start_time
        progress = offset / total_articles * 100
        rate = offset / elapsed if elapsed > 0 else 0
        eta = (total_articles - offset) / rate / 60 if rate > 0 else 0

        print(f"[{progress:5.1f}%] Processed {offset:,}/{total_articles:,} articles | "
              f"{len(citations_batch):,} citations | "
              f"{rate:.0f} articles/s | "
              f"ETA: {eta:.1f}m", end='\r')

    print()
    print("-"*60)

    elapsed_total = time.time() - start_time

    print()
    print("="*60)
    print("Complete!")
    print("="*60)
    print(f"Processed: {total_articles:,} articles")
    print(f"Extracted: {total_citations:,} citations")
    print(f"Time: {elapsed_total/60:.1f} minutes")
    print(f"Rate: {total_articles/elapsed_total:.0f} articles/second")
    print()
    print("Now you can use fast IF calculations with:")
    print("  python .dev/calculate_journals_with_citation_index.py 2023")

    conn.close()

if __name__ == "__main__":
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2023
    build_citation_index(year)
