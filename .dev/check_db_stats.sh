#!/bin/bash
# Check database statistics and index usage

# Get script directory and set relative path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="$SCRIPT_DIR/../data/crossref.db"

echo "=== Database File Info ==="
ls -lh "$DB_PATH"
echo ""

echo "=== Table Row Counts ==="
sqlite3 "$DB_PATH" "SELECT COUNT(*) as total_works FROM works;"
echo ""

echo "=== Index List ==="
sqlite3 "$DB_PATH" "SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='works';"
echo ""

echo "=== Sample Year Distribution (quick check) ==="
sqlite3 "$DB_PATH" "SELECT json_extract(metadata, '\$.published.date-parts[0][0]') as year, COUNT(*) as count FROM works WHERE id IN (SELECT id FROM works LIMIT 10000) GROUP BY year ORDER BY count DESC LIMIT 10;"
echo ""

echo "=== Test Index Usage ==="
echo "Query plan for year lookup:"
sqlite3 "$DB_PATH" "EXPLAIN QUERY PLAN SELECT COUNT(*) FROM works WHERE json_extract(metadata, '\$.published.date-parts[0][0]') = 2021;"
echo ""

echo "=== Database VACUUM Status ==="
sqlite3 "$DB_PATH" "PRAGMA page_count; PRAGMA freelist_count; PRAGMA page_size;"
