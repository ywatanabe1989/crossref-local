#!/usr/bin/env python3
"""
Test different approaches to count citations for speed optimization
"""

import sqlite3
import time
import os
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "../data/crossref.db"

# Test DOIs from Nature 2021 (sample)
test_dois = [
    "10.1038/s41586-021-03819-2",
    "10.1038/s41586-021-03207-w",
    "10.1038/s41586-021-03544-w"
]

conn = sqlite3.connect(DB_PATH)

print("="*60)
print("Citation Query Optimization Tests")
print("="*60)
print(f"Database: {DB_PATH}")
print(f"Testing with {len(test_dois)} sample DOIs")
print()

# Approach 1: Current method - scan all 2023 articles
print("Approach 1: Scan all 2023 articles with references")
print("-"*60)

query1 = """
SELECT COUNT(*)
FROM works
WHERE json_extract(metadata, '$.published.date-parts[0][0]') = 2023
AND json_extract(metadata, '$.reference') IS NOT NULL
"""

start = time.time()
cursor = conn.execute(query1)
count = cursor.fetchone()[0]
elapsed1 = time.time() - start

print(f"Articles with references in 2023: {count:,}")
print(f"Time: {elapsed1:.2f}s")
print(f"Estimated time for full scan: {elapsed1:.2f}s")
print()

# Approach 2: Check if we can query by referenced DOI (if indexed)
print("Approach 2: Direct lookup by referenced DOI")
print("-"*60)

# This would be ideal but requires parsing all reference fields
# Let's test if it's possible
query2 = """
SELECT metadata
FROM works
WHERE json_extract(metadata, '$.published.date-parts[0][0]') = 2023
AND json_extract(metadata, '$.reference') IS NOT NULL
LIMIT 1000
"""

start = time.time()
cursor = conn.execute(query2)

citation_count = 0
for row in cursor:
    import json
    metadata = json.loads(row[0])
    refs = metadata.get('reference', [])
    for ref in refs:
        if ref.get('DOI', '').lower() in [d.lower() for d in test_dois]:
            citation_count += 1

elapsed2 = time.time() - start

print(f"Scanned 1000 articles in: {elapsed2:.2f}s")
print(f"Found {citation_count} citations to test DOIs")
print(f"Estimated time for {count:,} articles: {elapsed2 * count / 1000 / 60:.1f} minutes")
print()

# Approach 3: Check database size and estimate
print("Approach 3: Database statistics")
print("-"*60)

query3 = """
SELECT
    COUNT(*) as total,
    SUM(CASE WHEN json_extract(metadata, '$.published.date-parts[0][0]') = 2023 THEN 1 ELSE 0 END) as year_2023
FROM works
"""

start = time.time()
cursor = conn.execute(query3)
result = cursor.fetchone()
elapsed3 = time.time() - start

print(f"Total works: {result[0]:,}")
print(f"Works in 2023: {result[1]:,}")
print(f"Query time: {elapsed3:.2f}s")
print()

# Recommendation
print("="*60)
print("RECOMMENDATIONS")
print("="*60)
print()

articles_per_second = 1000 / elapsed2
total_time_minutes = count / articles_per_second / 60

print(f"Current reference-graph method:")
print(f"  - Processing speed: ~{articles_per_second:.0f} articles/second")
print(f"  - Estimated time for all 2023: ~{total_time_minutes:.1f} minutes")
print(f"  - With 8 parallel workers: ~{total_time_minutes/8:.1f} minutes")
print()

print(f"Possible optimizations:")
print(f"  1. ✓ Parallel processing (already implemented)")
print(f"  2. Create materialized citation table (preprocessing)")
print(f"  3. Use sampling for large journals (statistical approximation)")
print(f"  4. Cache results for repeated calculations")

conn.close()
