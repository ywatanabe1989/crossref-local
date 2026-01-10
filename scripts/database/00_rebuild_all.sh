#!/bin/bash
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-08 03:15:00 (ywatanabe)"
# File: scripts/database/00_rebuild_all.sh
# Description: Full database rebuild from Crossref Public Data File
#
# TIMELINE (approximate):
#   Step 1: Load works      - 2-3 days
#   Step 2: Create indices  - 4-8 hours
#   Step 3: Build citations - 5-7 days
#   Step 4: Load journals   - 1 hour
#   Step 5: Build FTS       - 1-2 days
#   TOTAL: ~10-14 days
#
# REQUIREMENTS:
#   - 2TB+ disk space
#   - Crossref Public Data File downloaded to data/
#   - Python 3.11+ with venv
#   - sqlite3

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DATA_DIR="${PROJECT_ROOT}/data"
DB_PATH="${DATA_DIR}/crossref.db"
SOURCE_DIR="${DATA_DIR}/March 2025 Public Data File from Crossref"
VENDOR_DIR="${PROJECT_ROOT}/vendor/dois2sqlite"
LOG_DIR="${PROJECT_ROOT}/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log() { echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARNING]${NC} $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS] [STEP]

Rebuild CrossRef database from scratch.

STEPS:
    all         Run all steps (default)
    works       Step 1: Load works from Crossref data files
    indices     Step 2: Create indices on works table
    citations   Step 3: Build citations table
    journals    Step 4: Download and load journal data
    fts         Step 5: Build full-text search index

OPTIONS:
    -n, --dry-run    Show what would be done without executing
    -f, --force      Overwrite existing database
    -h, --help       Show this help

PREREQUISITES:
    1. Download Crossref Public Data File:
       https://academictorrents.com/details/e4287cb7619999709f6e9db5c359dda17e93d515

    2. Extract to: ${SOURCE_DIR}/

    3. Install dois2sqlite:
       cd ${VENDOR_DIR}
       pip install -e .

EXAMPLE:
    # Full rebuild (WARNING: ~10-14 days)
    screen -S rebuild
    ./scripts/database/00_rebuild_all.sh all
    # Ctrl-A D to detach

    # Just rebuild FTS index
    ./scripts/database/00_rebuild_all.sh fts
EOF
}

check_prerequisites() {
    log "Checking prerequisites..."

    # Check source data
    if [[ ! -d "$SOURCE_DIR" ]]; then
        error "Source data not found: $SOURCE_DIR"
        echo "Download from: https://academictorrents.com/details/e4287cb7619999709f6e9db5c359dda17e93d515"
        exit 1
    fi

    file_count=$(ls "$SOURCE_DIR"/*.jsonl.gz 2>/dev/null | wc -l)
    if [[ "$file_count" -lt 30000 ]]; then
        warn "Expected ~33,000 source files, found $file_count"
    fi

    # Check disk space
    available_gb=$(df -BG "$DATA_DIR" | tail -1 | awk '{print $4}' | tr -d 'G')
    if [[ "$available_gb" -lt 2000 ]]; then
        warn "Low disk space: ${available_gb}GB available, recommend 2TB+"
    fi

    log "Prerequisites OK"
}

step_works() {
    log "=== Step 1: Loading works from Crossref data ==="
    log "This will take 2-3 days..."

    mkdir -p "$LOG_DIR"

    if [[ -f "$DB_PATH" ]] && [[ "${FORCE:-}" != "1" ]]; then
        error "Database exists: $DB_PATH"
        echo "Use --force to overwrite or remove manually"
        exit 1
    fi

    # Create database
    cd "$VENDOR_DIR"
    source .venv/bin/activate 2>/dev/null || source venv/bin/activate

    dois2sqlite create "$DB_PATH"
    dois2sqlite load "$DB_PATH" "$SOURCE_DIR" 2>&1 | tee "$LOG_DIR/step1_works.log"

    log "Step 1 complete: works table loaded"
}

step_indices() {
    log "=== Step 2: Creating indices ==="
    log "This will take 4-8 hours..."

    sqlite3 "$DB_PATH" << 'SQL'
CREATE INDEX IF NOT EXISTS idx_doi_lookup ON works(doi);
CREATE INDEX IF NOT EXISTS idx_type ON works(type);
CREATE INDEX IF NOT EXISTS idx_container_title ON works(json_extract(metadata, '$.container-title[0]'));
CREATE INDEX IF NOT EXISTS idx_issn ON works(json_extract(metadata, '$.ISSN[0]'));
CREATE INDEX IF NOT EXISTS idx_published_year ON works(json_extract(metadata, '$.published.date-parts[0][0]'));
CREATE INDEX IF NOT EXISTS idx_issn_year ON works(json_extract(metadata, '$.ISSN[0]'), json_extract(metadata, '$.published.date-parts[0][0]'));
ANALYZE;
SQL

    log "Step 2 complete: indices created"
}

step_citations() {
    log "=== Step 3: Building citations table ==="
    log "This will take 5-7 days..."

    cd "$PROJECT_ROOT"
    source .venv/bin/activate

    python3 "$SCRIPT_DIR/03_rebuild_citations_table.py" 2>&1 | tee "$LOG_DIR/step3_citations.log"

    log "Step 3 complete: citations table built"
}

step_journals() {
    log "=== Step 4: Loading journal data from OpenAlex ==="
    log "This will take ~1 hour..."

    cd "$PROJECT_ROOT"
    source .venv/bin/activate

    python3 "$SCRIPT_DIR/04a_download_openalex_journals.py" 2>&1 | tee "$LOG_DIR/step4_journals.log"
    python3 "$SCRIPT_DIR/04b_build_issn_table.py" 2>&1 | tee -a "$LOG_DIR/step4_journals.log"

    log "Step 4 complete: journals loaded"
}

step_fts() {
    log "=== Step 5: Building FTS5 full-text search index ==="
    log "This will take 1-2 days..."

    cd "$PROJECT_ROOT"
    source .venv/bin/activate

    python3 "$SCRIPT_DIR/05_build_fts5_index.py" 2>&1 | tee "$LOG_DIR/step5_fts.log"

    log "Step 5 complete: FTS index built"
}

# Parse arguments
DRY_RUN=0
FORCE=0
STEP="all"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -n|--dry-run) DRY_RUN=1; shift ;;
        -f|--force) FORCE=1; shift ;;
        -h|--help) usage; exit 0 ;;
        all|works|indices|citations|journals|fts) STEP="$1"; shift ;;
        *) error "Unknown option: $1"; usage; exit 1 ;;
    esac
done

# Main
log "CrossRef Database Rebuild"
log "========================="
log "Step: $STEP"
log "DB Path: $DB_PATH"
log "Source: $SOURCE_DIR"

if [[ "$DRY_RUN" == "1" ]]; then
    warn "DRY RUN - no changes will be made"
    check_prerequisites
    exit 0
fi

check_prerequisites

case "$STEP" in
    all)
        step_works
        step_indices
        step_citations
        step_journals
        step_fts
        ;;
    works) step_works ;;
    indices) step_indices ;;
    citations) step_citations ;;
    journals) step_journals ;;
    fts) step_fts ;;
esac

log "========================================"
log "Database rebuild complete!"
log "Final size: $(du -h "$DB_PATH" | cut -f1)"
log "========================================"
