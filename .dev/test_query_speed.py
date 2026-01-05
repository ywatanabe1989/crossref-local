#!/usr/bin/env python3
"""
Test query speed with different approaches
"""

import sqlite3
import time
import json
import os

# Get relative path to database
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "../data/crossref.db")

def time_query(name, query, params=()):
    """Time a query execution"""
    conn = sqlite3.connect(DB_PATH)
    print(f"\n=== {name} ===")
    print(f"Query: {query}")
    print(f"Params: {params}")

    start = time.time()
    cursor = conn.execute(query, params)

    # Fetch first 10 results or count
    try:
        results = cursor.fetchmany(10)
        count = len(results)
    except:
        count = "N/A"

    elapsed = time.time() - start
    print(f"Time: {elapsed:.3f}s")
    print(f"Results (first 10): {count}")
    conn.close()
    return elapsed

# Test 1: Count all works
print("=" * 60)
print("DATABASE QUERY SPEED TESTS")
print("=" * 60)

time_query(
    "Count all works",
    "SELECT COUNT(*) FROM works"
)

# Test 2: Count by type (indexed column)
time_query(
    "Count by type (indexed column)",
    "SELECT COUNT(*) FROM works WHERE type = 'journal-article'"
)

# Test 3: Count by year (indexed expression)
time_query(
    "Count by year 2021 (indexed expression)",
    "SELECT COUNT(*) FROM works WHERE json_extract(metadata, '$.published.date-parts[0][0]') = 2021",
    (2021,)
)

# Test 4: Get Nature articles in 2021 (full query)
time_query(
    "Get Nature articles in 2021",
    """SELECT doi
       FROM works
       WHERE json_extract(metadata, '$.container-title[0]') LIKE '%Nature%'
       AND json_extract(metadata, '$.published.date-parts[0][0]') = 2021
       AND type = 'journal-article'
       LIMIT 100""",
)

# Test 5: Check if ANALYZE has been run
conn = sqlite3.connect(DB_PATH)
cursor = conn.execute("SELECT COUNT(*) FROM sqlite_stat1")
stat_count = cursor.fetchone()[0]
print(f"\n=== Database Statistics ===")
print(f"sqlite_stat1 entries: {stat_count}")
if stat_count == 0:
    print("WARNING: ANALYZE has not been run! Indexes may not be optimized.")
else:
    print("Database statistics are available.")
conn.close()

print("\n" + "=" * 60)
print("RECOMMENDATIONS:")
print("=" * 60)
print("If queries are slow:")
print("1. Run: sqlite3 /mnt/nas_ug/crossref_local/data/crossref.db 'ANALYZE;'")
print("2. Check if database needs VACUUM")
print("3. Consider adding more specific indexes")
