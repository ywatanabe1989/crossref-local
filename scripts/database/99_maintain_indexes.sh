#!/bin/bash
# -*- coding: utf-8 -*-
# File: scripts/database/99_maintain_indexes.sh
# Description: Check and create missing database indexes

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
LOG_PATH="${PROJECT_ROOT}/logs/maintain_indexes_$(date +%Y%m%d).log"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
LIGHT_GRAY='\033[0;37m'
NC='\033[0m'

echo_info() { echo -e "${LIGHT_GRAY}$1${NC}"; }
echo_success() { echo -e "${GREEN}$1${NC}"; }
echo_warning() { echo -e "${YELLOW}$1${NC}"; }
echo_error() { echo -e "${RED}$1${NC}"; }

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] [DB_PATH]

Check and create missing database indexes for crossref.db.

ARGUMENTS:
    DB_PATH    Path to database (default: \$CROSSREF_LOCAL_DB or data/crossref.db)

OPTIONS:
    -c, --check-only   Only check indexes, don't create missing ones
    -h, --help         Show this help message

EXAMPLES:
    $(basename "$0")                    # Check/create on default database
    $(basename "$0") /path/to/db        # Custom database path
    $(basename "$0") --check-only       # Only check, don't modify

NOTE:
    Index creation can take hours for large databases.
    Recommended to run in screen session for long operations.
EOF
}

# Parse arguments
CHECK_ONLY=0
DB_PATH=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        -c|--check-only) CHECK_ONLY=1; shift ;;
        -h|--help) usage; exit 0 ;;
        -*) echo_error "Unknown option: $1"; usage; exit 1 ;;
        *) DB_PATH="$1"; shift ;;
    esac
done

# Set default DB path
DB_PATH="${DB_PATH:-${CROSSREF_LOCAL_DB:-${PROJECT_ROOT}/data/crossref.db}}"

mkdir -p "$(dirname "$LOG_PATH")"
echo > "$LOG_PATH"

echo_info "=========================================="
echo_info "CrossRef Database Index Maintenance"
echo_info "=========================================="
echo_info ""
echo_info "Database: $DB_PATH"
echo_info ""

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo_error "ERROR: Database not found at $DB_PATH"
    exit 1
fi

# Check database size
DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
echo_info "Database size: $DB_SIZE"
echo_info ""

# Function to check if index exists
check_index() {
    local index_name=$1
    local result=$(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='index' AND name='$index_name';")
    if [ -n "$result" ]; then
        return 0
    else
        return 1
    fi
}

# Function to create index with progress
create_index_with_progress() {
    local index_name=$1
    local index_sql=$2

    echo_info "Creating index: $index_name"
    echo_info "SQL: $index_sql"
    echo_info "This may take a long time (hours)..."
    echo_info ""

    # Create index and log to file
    sqlite3 "$DB_PATH" "$index_sql" 2>&1 | tee -a "$LOG_PATH"

    if [ $? -eq 0 ]; then
        echo_success "✓ Index created successfully: $index_name"
    else
        echo_error "✗ Failed to create index: $index_name"
        return 1
    fi

    echo_info ""
}

# Check existing indexes
echo_info "Checking existing indexes..."
echo_info ""

INDEXES_TO_CREATE=()

# Check each required index
if check_index "idx_container_title"; then
    echo_success "✓ idx_container_title exists"
else
    echo_warning "✗ idx_container_title missing"
    INDEXES_TO_CREATE+=("idx_container_title")
fi

if check_index "idx_issn"; then
    echo_success "✓ idx_issn exists"
else
    echo_warning "✗ idx_issn missing"
    INDEXES_TO_CREATE+=("idx_issn")
fi

if check_index "idx_published_year"; then
    echo_success "✓ idx_published_year exists"
else
    echo_warning "✗ idx_published_year missing"
    INDEXES_TO_CREATE+=("idx_published_year")
fi

if check_index "idx_doi_lookup"; then
    echo_success "✓ idx_doi_lookup exists"
else
    echo_warning "✗ idx_doi_lookup missing"
    INDEXES_TO_CREATE+=("idx_doi_lookup")
fi

if check_index "idx_type"; then
    echo_success "✓ idx_type exists"
else
    echo_warning "✗ idx_type missing"
    INDEXES_TO_CREATE+=("idx_type")
fi

# Check citation index table
echo_info ""
echo_info "Checking citation index table..."
CITATIONS_TABLE_EXISTS=$(sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='citations';")
if [ -n "$CITATIONS_TABLE_EXISTS" ]; then
    echo_success "✓ citations table exists"

    # Check which years are indexed
    INDEXED_YEARS=$(sqlite3 "$DB_PATH" "SELECT DISTINCT citing_year FROM citations ORDER BY citing_year;")
    if [ -n "$INDEXED_YEARS" ]; then
        echo_info "  Indexed years: $(echo $INDEXED_YEARS | tr '\n' ' ')"
    fi
else
    echo_warning "✗ citations table missing"
fi

echo_info ""

# If all indexes exist, offer to build citation index
if [ ${#INDEXES_TO_CREATE[@]} -eq 0 ]; then
    echo_success "=========================================="
    echo_success "All basic indexes are present!"
    echo_success "=========================================="
    echo_info ""

    # Ask about citation index
    if [ -z "$CITATIONS_TABLE_EXISTS" ]; then
        echo_warning "Citation index not found."
        echo_info ""
        echo_info "The citation index enables fast, accurate impact factor calculations"
        echo_info "by pre-computing citation relationships."
        echo_info ""
        echo_warning "Building the citation index for one year takes ~30-60 minutes,"
        echo_warning "but makes IF calculations instant instead of timing out."
        echo_info ""
        read -p "Build citation index for which year? (e.g., 2023, or press Enter to skip): " CITATION_YEAR

        if [ -n "$CITATION_YEAR" ]; then
            echo_info ""
            echo_info "Building citation index for year $CITATION_YEAR..."
            python3 "$(dirname $0)/../../.dev/build_citation_index.py" "$CITATION_YEAR"
        fi
    else
        echo_info "Citation index years available: $(echo $INDEXED_YEARS | tr '\n' ' ')"
        echo_info ""
        read -p "Build citation index for additional year? (e.g., 2024, or press Enter to skip): " CITATION_YEAR

        if [ -n "$CITATION_YEAR" ]; then
            # Check if year already indexed
            YEAR_EXISTS=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM citations WHERE citing_year = $CITATION_YEAR;")
            if [ "$YEAR_EXISTS" -gt 0 ]; then
                echo_warning "Year $CITATION_YEAR already has $YEAR_EXISTS citations indexed."
                read -p "Rebuild anyway? [y/N]: " -n 1 -r
                echo
                if [[ $REPLY =~ ^[Yy]$ ]]; then
                    python3 "$(dirname $0)/../../.dev/build_citation_index.py" "$CITATION_YEAR"
                fi
            else
                python3 "$(dirname $0)/../../.dev/build_citation_index.py" "$CITATION_YEAR"
            fi
        fi
    fi

    echo_info ""
    echo_info "Database statistics:"
    sqlite3 "$DB_PATH" "ANALYZE;" 2>&1 | tee -a "$LOG_PATH"
    echo_info ""
    echo_info "Index list:"
    sqlite3 "$DB_PATH" "SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY name;" | column -t -s '|'
    echo_info ""
    echo_success "Log saved to: $LOG_PATH"
    exit 0
fi

# Ask user if they want to create missing indexes
echo_warning "=========================================="
echo_warning "Missing ${#INDEXES_TO_CREATE[@]} index(es)"
echo_warning "=========================================="
echo_info ""
echo_warning "Creating indexes will take a LONG time (potentially hours)"
echo_warning "Database size: $DB_SIZE"
echo_warning "But queries will be MUCH faster afterward"
echo_info ""
read -p "Do you want to create missing indexes? [y/N] " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo_info "Index creation cancelled."
    echo_info ""
    echo_info "To create indexes later, run:"
    echo_info "  $0 $DB_PATH"
    exit 0
fi

# Create missing indexes
echo_info ""
echo_info "=========================================="
echo_info "Creating Indexes"
echo_info "=========================================="
echo_info ""
echo_info "Start time: $(date)"
echo_info ""

START_TIME=$(date +%s)

for index_name in "${INDEXES_TO_CREATE[@]}"; do
    case $index_name in
        idx_container_title)
            create_index_with_progress \
                "idx_container_title" \
                "CREATE INDEX IF NOT EXISTS idx_container_title ON works(json_extract(metadata, '\$.container-title[0]'));"
            ;;
        idx_issn)
            create_index_with_progress \
                "idx_issn" \
                "CREATE INDEX IF NOT EXISTS idx_issn ON works(json_extract(metadata, '\$.ISSN[0]'));"
            ;;
        idx_published_year)
            create_index_with_progress \
                "idx_published_year" \
                "CREATE INDEX IF NOT EXISTS idx_published_year ON works(json_extract(metadata, '\$.published.date-parts[0][0]'));"
            ;;
        idx_doi_lookup)
            create_index_with_progress \
                "idx_doi_lookup" \
                "CREATE INDEX IF NOT EXISTS idx_doi_lookup ON works(doi);"
            ;;
        idx_type)
            create_index_with_progress \
                "idx_type" \
                "CREATE INDEX IF NOT EXISTS idx_type ON works(type);"
            ;;
    esac
done

# Run ANALYZE to update statistics
echo_info "Updating database statistics..."
sqlite3 "$DB_PATH" "ANALYZE;" 2>&1 | tee -a "$LOG_PATH"
echo_success "✓ Statistics updated"
echo_info ""

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))
SECONDS=$((ELAPSED % 60))

echo_success "=========================================="
echo_success "Index Creation Complete!"
echo_success "=========================================="
echo_info ""
echo_info "End time: $(date)"
echo_info "Total time: ${HOURS}h ${MINUTES}m ${SECONDS}s"
echo_info ""
echo_success "Queries will now be much faster!"
echo_info ""
echo_info "Verify indexes:"
echo_info "  sqlite3 $DB_PATH \"SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY name;\""
echo_info ""
echo_success "Log saved to: $LOG_PATH"

# EOF