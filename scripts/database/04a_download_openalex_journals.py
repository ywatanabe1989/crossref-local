#!/usr/bin/env python3
"""
Download journal data from OpenAlex (open, legitimate source).

OpenAlex provides ~222k journals with:
- ISSN (multiple variants)
- Display name + alternate titles (handles abbreviations)
- 2yr_mean_citedness (similar to Impact Factor)
- h_index, works_count, cited_by_count

Usage:
    python download_openalex_journals.py --db /path/to/crossref.db
    python download_openalex_journals.py --output journals.json  # JSON only
"""

import argparse
import json
import logging
import sqlite3
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BASE_URL = "https://api.openalex.org/sources"
USER_AGENT = "CrossRefLocal/1.0 (mailto:research@example.com)"


def fetch_page(cursor: str = "*", per_page: int = 200) -> dict:
    """Fetch one page of journal data from OpenAlex."""
    url = f"{BASE_URL}?filter=type:journal&per_page={per_page}&cursor={cursor}"
    req = Request(url, headers={"User-Agent": USER_AGENT})

    for attempt in range(3):
        try:
            with urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode())
        except HTTPError as e:
            if e.code == 429:  # Rate limit
                wait = 2 ** attempt
                logger.warning(f"Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                raise
    raise Exception("Max retries exceeded")


def download_all_journals() -> list:
    """Download all journals from OpenAlex."""
    all_journals = []
    cursor = "*"
    page = 0

    # Get total count
    first_page = fetch_page(cursor, per_page=1)
    total = first_page["meta"]["count"]
    logger.info(f"Total journals to download: {total:,}")

    while cursor:
        page += 1
        data = fetch_page(cursor, per_page=200)

        for source in data["results"]:
            journal = {
                "openalex_id": source["id"],
                "issn_l": source.get("issn_l"),
                "issns": source.get("issn", []),
                "name": source.get("display_name"),
                "alternate_titles": source.get("alternate_titles", []),
                "publisher": source.get("host_organization_name"),
                "country": source.get("country_code"),
                "works_count": source.get("works_count", 0),
                "cited_by_count": source.get("cited_by_count", 0),
                "two_year_mean_citedness": source.get("summary_stats", {}).get("2yr_mean_citedness"),
                "h_index": source.get("summary_stats", {}).get("h_index"),
                "is_oa": source.get("is_oa", False),
                "is_in_doaj": source.get("is_in_doaj", False),
                "homepage_url": source.get("homepage_url"),
            }
            all_journals.append(journal)

        # Progress
        downloaded = len(all_journals)
        logger.info(f"Downloaded {downloaded:,}/{total:,} journals ({100*downloaded/total:.1f}%)")

        # Next cursor
        cursor = data["meta"].get("next_cursor")

        # Be nice to API
        time.sleep(0.1)

    return all_journals


def save_to_json(journals: list, output_path: str):
    """Save journals to JSON file."""
    with open(output_path, "w") as f:
        json.dump(journals, f, indent=2)
    logger.info(f"Saved {len(journals):,} journals to {output_path}")


def save_to_sqlite(journals: list, db_path: str):
    """Save journals to SQLite database."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop and recreate table
    cursor.execute("DROP TABLE IF EXISTS journals_openalex")
    cursor.execute("""
        CREATE TABLE journals_openalex (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            openalex_id TEXT UNIQUE,
            issn_l TEXT,
            issns TEXT,  -- JSON array
            name TEXT,
            name_lower TEXT,
            alternate_titles TEXT,  -- JSON array
            publisher TEXT,
            country TEXT,
            works_count INTEGER,
            cited_by_count INTEGER,
            two_year_mean_citedness REAL,  -- Similar to Impact Factor
            h_index INTEGER,
            is_oa BOOLEAN,
            is_in_doaj BOOLEAN,
            homepage_url TEXT
        )
    """)

    # Insert data
    for j in journals:
        cursor.execute("""
            INSERT INTO journals_openalex (
                openalex_id, issn_l, issns, name, name_lower, alternate_titles,
                publisher, country, works_count, cited_by_count,
                two_year_mean_citedness, h_index, is_oa, is_in_doaj, homepage_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            j["openalex_id"],
            j["issn_l"],
            json.dumps(j["issns"]),
            j["name"],
            j["name"].lower() if j["name"] else None,
            json.dumps(j["alternate_titles"]),
            j["publisher"],
            j["country"],
            j["works_count"],
            j["cited_by_count"],
            j["two_year_mean_citedness"],
            j["h_index"],
            j["is_oa"],
            j["is_in_doaj"],
            j["homepage_url"],
        ))

    conn.commit()

    # Create indexes
    logger.info("Creating indexes...")
    cursor.execute("CREATE INDEX idx_openalex_issn_l ON journals_openalex(issn_l)")
    cursor.execute("CREATE INDEX idx_openalex_name_lower ON journals_openalex(name_lower)")
    cursor.execute("CREATE INDEX idx_openalex_name ON journals_openalex(name)")
    conn.commit()

    # Also create ISSN lookup table (one row per ISSN)
    logger.info("Creating ISSN lookup table...")
    cursor.execute("DROP TABLE IF EXISTS issn_lookup")
    cursor.execute("""
        CREATE TABLE issn_lookup (
            issn TEXT PRIMARY KEY,
            journal_id INTEGER,
            FOREIGN KEY (journal_id) REFERENCES journals_openalex(id)
        )
    """)

    # Populate ISSN lookup
    cursor.execute("SELECT id, issns FROM journals_openalex")
    for row in cursor.fetchall():
        journal_id = row[0]
        issns = json.loads(row[1]) if row[1] else []
        for issn in issns:
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO issn_lookup (issn, journal_id) VALUES (?, ?)",
                    (issn, journal_id)
                )
            except sqlite3.IntegrityError:
                pass  # Duplicate ISSN

    conn.commit()
    cursor.execute("SELECT COUNT(*) FROM issn_lookup")
    issn_count = cursor.fetchone()[0]

    logger.info(f"Saved {len(journals):,} journals with {issn_count:,} ISSNs to {db_path}")
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Download OpenAlex journal data")
    parser.add_argument("--db", help="SQLite database path")
    parser.add_argument("--output", help="JSON output file")
    args = parser.parse_args()

    if not args.db and not args.output:
        args.db = "./data/crossref.db"

    logger.info("Downloading journals from OpenAlex...")
    start = time.time()

    journals = download_all_journals()

    if args.output:
        save_to_json(journals, args.output)

    if args.db:
        save_to_sqlite(journals, args.db)

    elapsed = time.time() - start
    logger.info(f"Done in {elapsed/60:.1f} minutes")

    # Show sample
    logger.info("\nTop 10 journals by 2-year mean citedness (Impact Factor proxy):")
    sorted_journals = sorted(
        [j for j in journals if j["two_year_mean_citedness"]],
        key=lambda x: x["two_year_mean_citedness"] or 0,
        reverse=True
    )[:10]
    for j in sorted_journals:
        logger.info(
            f"  {j['name'][:45]:<45} "
            f"IF≈{j['two_year_mean_citedness']:>6.1f}  "
            f"ISSN: {j['issn_l'] or 'N/A'}"
        )


if __name__ == "__main__":
    main()
