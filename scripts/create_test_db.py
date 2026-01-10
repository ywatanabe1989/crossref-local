#!/usr/bin/env python3
"""
Create test database from CrossRef API samples.

Downloads sample works from CrossRef API and builds a small test database
with FTS5 index for reproducible testing.

Usage:
    python scripts/create_test_db.py
    python scripts/create_test_db.py --rows 500
"""

import argparse
import json
import sqlite3
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from urllib.parse import quote

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
TEST_DB_PATH = PROJECT_ROOT / "tests" / "fixtures" / "test_crossref.db"
SAMPLE_JSON_PATH = PROJECT_ROOT / "tests" / "fixtures" / "sample_works.json"

# CrossRef API
CROSSREF_API = "https://api.crossref.org/works"
USER_AGENT = "crossref-local-tests/0.1 (https://github.com/ywatanabe1989/crossref_local)"


def download_sample_works(rows: int = 1000, queries: list = None) -> list:
    """
    Download sample works from CrossRef API.

    Args:
        rows: Number of records per query
        queries: List of search queries for diversity

    Returns:
        List of work metadata dictionaries
    """
    if queries is None:
        # Diverse queries to get varied content
        queries = [
            "neuroscience",
            "machine learning",
            "climate change",
            "cancer",
            "quantum",
        ]

    all_works = []
    rows_per_query = rows // len(queries)

    for query in queries:
        print(f"Downloading '{query}' ({rows_per_query} records)...")

        url = f"{CROSSREF_API}?query={quote(query)}&rows={rows_per_query}"
        req = Request(url, headers={"User-Agent": USER_AGENT})

        try:
            with urlopen(req, timeout=60) as response:
                data = json.loads(response.read().decode())
                works = data.get("message", {}).get("items", [])
                all_works.extend(works)
                print(f"  Got {len(works)} records")
        except HTTPError as e:
            print(f"  Error: {e}")

        # Be nice to the API
        time.sleep(1)

    print(f"Total: {len(all_works)} records")
    return all_works


def save_sample_json(works: list, path: Path):
    """Save works to JSON file for reproducibility."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(works, f)
    print(f"Saved JSON: {path} ({path.stat().st_size / 1024:.1f} KB)")


def load_sample_json(path: Path) -> list:
    """Load works from JSON file."""
    with open(path) as f:
        return json.load(f)


def create_database(works: list, db_path: Path):
    """
    Create SQLite database with same schema as main crossref.db.

    Args:
        works: List of work metadata dictionaries
        db_path: Path to output database
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove existing
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create works table (same schema as main DB)
    cursor.execute("""
        CREATE TABLE works (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doi VARCHAR(255),
            resource_primary_url VARCHAR(255),
            type VARCHAR(255),
            member INTEGER,
            prefix VARCHAR(8),
            created_date_time DATE,
            deposited_date_time DATE,
            commonmeta_format BOOLEAN,
            metadata TEXT
        )
    """)

    # Create indices
    cursor.execute("CREATE INDEX idx_doi_lookup ON works(doi)")
    cursor.execute("CREATE INDEX idx_type ON works(type)")

    # Insert works
    print(f"Inserting {len(works)} works...")
    for work in works:
        doi = work.get("DOI", "")
        url = work.get("URL", "")
        work_type = work.get("type", "")
        member = work.get("member")
        prefix = work.get("prefix", "")[:8] if work.get("prefix") else None

        cursor.execute("""
            INSERT INTO works (doi, resource_primary_url, type, member, prefix, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (doi, url, work_type, member, prefix, json.dumps(work)))

    conn.commit()
    print(f"Inserted {len(works)} works")

    # Create FTS5 index
    print("Building FTS5 index...")
    cursor.execute("""
        CREATE VIRTUAL TABLE works_fts USING fts5(
            doi,
            title,
            abstract,
            authors,
            content='',
            tokenize='porter unicode61'
        )
    """)

    # Populate FTS index
    for work in works:
        doi = work.get("DOI", "")

        # Extract title
        titles = work.get("title", [])
        title = titles[0] if titles else ""

        # Extract abstract
        abstract = work.get("abstract", "")

        # Extract authors
        authors = []
        for author in work.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            if given and family:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)
        authors_str = ", ".join(authors)

        cursor.execute("""
            INSERT INTO works_fts (rowid, doi, title, abstract, authors)
            VALUES ((SELECT id FROM works WHERE doi = ?), ?, ?, ?, ?)
        """, (doi, doi, title, abstract, authors_str))

    conn.commit()

    # Create citations table (empty, for schema compatibility)
    cursor.execute("""
        CREATE TABLE citations (
            citing_doi TEXT NOT NULL,
            cited_doi TEXT NOT NULL,
            citing_year INTEGER NOT NULL
        )
    """)
    cursor.execute("CREATE INDEX idx_citations_cited_new ON citations(cited_doi, citing_year)")

    conn.commit()
    conn.close()

    print(f"Created database: {db_path} ({db_path.stat().st_size / 1024:.1f} KB)")


def verify_database(db_path: Path):
    """Verify the database works correctly."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check counts
    cursor.execute("SELECT COUNT(*) FROM works")
    works_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM works_fts")
    fts_count = cursor.fetchone()[0]

    print(f"\nVerification:")
    print(f"  Works: {works_count}")
    print(f"  FTS indexed: {fts_count}")

    # Test search
    cursor.execute("""
        SELECT COUNT(*) FROM works_fts WHERE works_fts MATCH 'neuroscience'
    """)
    search_count = cursor.fetchone()[0]
    print(f"  Search 'neuroscience': {search_count} matches")

    conn.close()

    if works_count > 0 and fts_count > 0:
        print("\nTest database ready!")
        return True
    else:
        print("\nError: Database verification failed")
        return False


def main():
    parser = argparse.ArgumentParser(description="Create test database from CrossRef API")
    parser.add_argument("--rows", type=int, default=1000, help="Number of records to download")
    parser.add_argument("--use-cached", action="store_true", help="Use cached JSON if available")
    args = parser.parse_args()

    print("=" * 60)
    print("Creating CrossRef Test Database")
    print("=" * 60)
    print()

    # Download or load sample works
    if args.use_cached and SAMPLE_JSON_PATH.exists():
        print(f"Using cached JSON: {SAMPLE_JSON_PATH}")
        works = load_sample_json(SAMPLE_JSON_PATH)
    else:
        works = download_sample_works(rows=args.rows)
        save_sample_json(works, SAMPLE_JSON_PATH)

    print()

    # Create database
    create_database(works, TEST_DB_PATH)

    # Verify
    verify_database(TEST_DB_PATH)

    print()
    print("=" * 60)
    print(f"Test database: {TEST_DB_PATH}")
    print("Run tests with: make test")
    print("=" * 60)


if __name__ == "__main__":
    main()
