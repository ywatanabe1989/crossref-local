#!/bin/bash
# Run ANALYZE on the database to update query planner statistics
# This is crucial for efficient index usage

# Get script directory and set relative path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="$SCRIPT_DIR/../data/crossref.db"

echo "=== Running ANALYZE on CrossRef database ==="
echo "Database: $DB_PATH"
echo ""
echo "This may take several minutes for large databases..."
echo ""

time sqlite3 "$DB_PATH" "ANALYZE;"

echo ""
echo "=== ANALYZE complete ==="
echo ""
echo "Checking statistics..."
sqlite3 "$DB_PATH" "SELECT COUNT(*) as stat_entries FROM sqlite_stat1;"
