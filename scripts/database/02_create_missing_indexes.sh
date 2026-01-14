#!/bin/bash
# -*- coding: utf-8 -*-
# File: scripts/database/02_create_missing_indexes.sh
# Description: Create missing indexes on citations table for impact factor calculations

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DB="${CROSSREF_LOCAL_DB:-${PROJECT_ROOT}/data/crossref.db}"
LOG_DIR="${PROJECT_ROOT}/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Create missing indexes on citations table for impact factor calculations.
Run in screen for long-running index creation.

OPTIONS:
    -d, --db PATH    Database path (default: \$CROSSREF_LOCAL_DB or data/crossref.db)
    -n, --dry-run    Show what would be done without executing
    -h, --help       Show this help message

EXAMPLES:
    $(basename "$0")                    # Create indexes on default database
    $(basename "$0") --db /path/to.db   # Custom database path

    # Long-running (use screen):
    screen -S index-rebuild
    $(basename "$0")
    # Ctrl-A D to detach
EOF
}

check_db() {
    if [[ ! -f "$DB" ]]; then
        echo -e "${RED}ERROR: Database not found: ${DB}${NC}" >&2
        exit 1
    fi
}

create_indexes() {
    local LOG="${LOG_DIR}/index_creation_$(date +%Y%m%d_%H%M%S).log"
    mkdir -p "$LOG_DIR"

    echo "=== Index Creation Started: $(date) ===" | tee -a "$LOG"
    echo "Database: $DB" | tee -a "$LOG"

    echo "" | tee -a "$LOG"
    echo "Checking existing indexes..." | tee -a "$LOG"
    sqlite3 "$DB" ".indexes citations" | tee -a "$LOG"

    echo "" | tee -a "$LOG"
    echo "[$(date)] Creating idx_citations_cited_new ON citations(cited_doi, citing_year)..." | tee -a "$LOG"
    time sqlite3 "$DB" "CREATE INDEX IF NOT EXISTS idx_citations_cited_new ON citations(cited_doi, citing_year);" 2>&1 | tee -a "$LOG"
    echo -e "${GREEN}[$(date)] idx_citations_cited_new completed${NC}" | tee -a "$LOG"

    echo "" | tee -a "$LOG"
    echo "[$(date)] Creating idx_citations_year_new ON citations(citing_year)..." | tee -a "$LOG"
    time sqlite3 "$DB" "CREATE INDEX IF NOT EXISTS idx_citations_year_new ON citations(citing_year);" 2>&1 | tee -a "$LOG"
    echo -e "${GREEN}[$(date)] idx_citations_year_new completed${NC}" | tee -a "$LOG"

    echo "" | tee -a "$LOG"
    echo "[$(date)] Verifying indexes..." | tee -a "$LOG"
    sqlite3 "$DB" ".indexes citations" | tee -a "$LOG"

    echo "" | tee -a "$LOG"
    echo "=== Index Creation Completed: $(date) ===" | tee -a "$LOG"
    echo "Log saved to: $LOG"
}

# Parse arguments
DRY_RUN=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--db) DB="$2"; shift 2 ;;
        -n|--dry-run) DRY_RUN=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; usage; exit 1 ;;
    esac
done

check_db

if [[ "$DRY_RUN" == "1" ]]; then
    echo -e "${YELLOW}DRY RUN - Would create indexes on: $DB${NC}"
    echo "Indexes to create:"
    echo "  - idx_citations_cited_new ON citations(cited_doi, citing_year)"
    echo "  - idx_citations_year_new ON citations(citing_year)"
    exit 0
fi

create_indexes
