#!/bin/bash
# Create missing indexes on citations table
# Run in screen: screen -S index-rebuild

DB="/home/ywatanabe/proj/crossref_local/data/crossref.db"
LOG="/home/ywatanabe/proj/crossref_local/impact_factor/index_creation_$(date +%Y%m%d_%H%M%S).log"

echo "=== Index Creation Started: $(date) ===" | tee -a "$LOG"
echo "Database: $DB" | tee -a "$LOG"

# Check if first index already exists
echo "" | tee -a "$LOG"
echo "Checking existing indexes..." | tee -a "$LOG"
sqlite3 "$DB" ".indexes citations" | tee -a "$LOG"

# Create idx_citations_cited_new (most important for IF calculations)
echo "" | tee -a "$LOG"
echo "[$(date)] Creating idx_citations_cited_new ON citations(cited_doi, citing_year)..." | tee -a "$LOG"
time sqlite3 "$DB" "CREATE INDEX IF NOT EXISTS idx_citations_cited_new ON citations(cited_doi, citing_year);" 2>&1 | tee -a "$LOG"
echo "[$(date)] idx_citations_cited_new completed" | tee -a "$LOG"

# Create idx_citations_year_new
echo "" | tee -a "$LOG"
echo "[$(date)] Creating idx_citations_year_new ON citations(citing_year)..." | tee -a "$LOG"
time sqlite3 "$DB" "CREATE INDEX IF NOT EXISTS idx_citations_year_new ON citations(citing_year);" 2>&1 | tee -a "$LOG"
echo "[$(date)] idx_citations_year_new completed" | tee -a "$LOG"

# Verify indexes
echo "" | tee -a "$LOG"
echo "[$(date)] Verifying indexes..." | tee -a "$LOG"
sqlite3 "$DB" ".indexes citations" | tee -a "$LOG"

# Test query plans
echo "" | tee -a "$LOG"
echo "Query plan for cited_doi lookup:" | tee -a "$LOG"
sqlite3 "$DB" "EXPLAIN QUERY PLAN SELECT * FROM citations WHERE cited_doi = '10.1056/NEJMoa1003466' LIMIT 1;" | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "Query plan for citing_year lookup:" | tee -a "$LOG"
sqlite3 "$DB" "EXPLAIN QUERY PLAN SELECT * FROM citations WHERE citing_year = 2024 LIMIT 1;" | tee -a "$LOG"

echo "" | tee -a "$LOG"
echo "=== Index Creation Completed: $(date) ===" | tee -a "$LOG"
