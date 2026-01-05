#!/bin/bash
# Add indexes to speed up reference-graph citation counting

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DB_PATH="$SCRIPT_DIR/../data/crossref.db"

echo "========================================"
echo "Adding Reference Indexes for Fast Citations"
echo "========================================"
echo "Database: $DB_PATH"
echo ""
echo "This will create indexes to speed up citation queries."
echo "WARNING: This may take 30-60 minutes for a large database."
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled"
    exit 1
fi

echo ""
echo "Creating indexes..."
echo "----------------------------------------"

# Index 1: Combined index on year + has references
echo "1. Creating index on (published_year, has_references)..."
time sqlite3 "$DB_PATH" "
CREATE INDEX IF NOT EXISTS idx_year_with_refs
ON works(json_extract(metadata, '\$.published.date-parts[0][0]'))
WHERE json_extract(metadata, '\$.reference') IS NOT NULL;
"
echo "✓ Done"
echo ""

# Check index usage
echo "Verifying index..."
sqlite3 "$DB_PATH" "
EXPLAIN QUERY PLAN
SELECT metadata
FROM works
WHERE json_extract(metadata, '\$.published.date-parts[0][0]') = 2023
AND json_extract(metadata, '\$.reference') IS NOT NULL;
"

echo ""
echo "========================================"
echo "Indexes Created Successfully"
echo "========================================"
echo ""
echo "Test the improvement with:"
echo "  python .dev/calculate_journals_from_csv_parallel.py 2023 8"
