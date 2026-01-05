#!/usr/bin/env python3
"""
Test a single query with detailed timing and explain plan
"""

import sqlite3
import time
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "../data/crossref.db")

print(f"Database: {DB_PATH}")
print(f"Connecting...")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Test query - Nature ISSN for 2021
issn = "0028-0836"
year = 2021

print(f"\n{'='*60}")
print(f"Test Query: Articles for ISSN {issn} in year {year}")
print(f"{'='*60}\n")

# First, check the query plan
query = """
SELECT doi, metadata
FROM works
WHERE json_extract(metadata, '$.ISSN[0]') = ?
AND json_extract(metadata, '$.published.date-parts[0][0]') = ?
AND type = 'journal-article'
"""

print("EXPLAIN QUERY PLAN:")
explain_cursor = conn.execute(f"EXPLAIN QUERY PLAN {query}", (issn, year))
for row in explain_cursor:
    print(f"  {dict(row)}")
print()

# Count matching rows first (faster than fetching all)
print("Counting matching articles...")
count_query = """
SELECT COUNT(*) as count
FROM works
WHERE json_extract(metadata, '$.ISSN[0]') = ?
AND json_extract(metadata, '$.published.date-parts[0][0]') = ?
AND type = 'journal-article'
"""

start = time.time()
cursor = conn.execute(count_query, (issn, year))
count = cursor.fetchone()[0]
elapsed = time.time() - start

print(f"Found {count} articles in {elapsed:.2f} seconds")
print()

# Check if ANALYZE has been run
print("Checking database statistics...")
cursor = conn.execute("SELECT COUNT(*) FROM sqlite_stat1 WHERE tbl='works'")
stat_count = cursor.fetchone()[0]
print(f"Index statistics entries: {stat_count}")

if stat_count == 0:
    print("\n⚠️  WARNING: ANALYZE has NOT been run!")
    print("   Run: .dev/run_analyze.sh")
    print("   This will significantly improve query performance.")
else:
    print("✓ Database statistics are available")

print()

# Check index cardinality
print("Index statistics:")
cursor = conn.execute("""
    SELECT idx, stat
    FROM sqlite_stat1
    WHERE tbl='works'
    ORDER BY idx
""")
for row in cursor:
    print(f"  {row[0]}: {row[1]}")

conn.close()

print(f"\n{'='*60}")
print("Summary:")
print(f"{'='*60}")
print(f"Query took: {elapsed:.2f}s for {count} articles")
if elapsed > 5:
    print("⚠️  Query is slow! Recommendations:")
    print("  1. Run ANALYZE: .dev/run_analyze.sh")
    print("  2. Check if the database file is on a slow disk (NAS)")
    print("  3. Consider copying database to local SSD for testing")
elif elapsed > 1:
    print("⚠️  Query is somewhat slow for large-scale calculations")
else:
    print("✓ Query performance is good")
