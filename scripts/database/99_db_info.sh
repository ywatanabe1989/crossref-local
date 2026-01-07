#!/bin/bash
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-08 03:00:00 (ywatanabe)"
# File: scripts/database/99_db_info.sh
# Description: Display database schema, tables, indices, and row counts
# Usage: ./scripts/database/99_db_info.sh [--full]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DB_PATH="${PROJECT_ROOT}/data/crossref.db"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Display database information for crossref.db

OPTIONS:
    -f, --full      Show full schema (CREATE statements)
    -t, --tables    Show only tables with row counts
    -i, --indices   Show only indices
    -s, --size      Show database file size
    -h, --help      Show this help message

EXAMPLES:
    $(basename "$0")           # Quick summary
    $(basename "$0") --full    # Full schema dump
    $(basename "$0") --tables  # Tables and counts only
EOF
}

check_db() {
    if [[ ! -f "$DB_PATH" ]]; then
        echo -e "${RED}ERROR: Database not found at ${DB_PATH}${NC}" >&2
        echo "Hint: Run 'make download' or check data symlink" >&2
        exit 1
    fi
}

show_size() {
    echo -e "${CYAN}=== Database Size ===${NC}"
    ls -lh "$DB_PATH" | awk '{print $5, $9}'
    echo
}

show_tables() {
    echo -e "${CYAN}=== Tables ===${NC}"
    printf "%-40s %15s\n" "TABLE" "ROWS (approx)"
    printf "%-40s %15s\n" "----------------------------------------" "---------------"

    # Get tables
    tables=$(sqlite3 "$DB_PATH" ".tables" | tr -s ' ' '\n' | grep -v '^$' | sort)

    for table in $tables; do
        # Skip FTS internal tables
        if [[ "$table" =~ ^works_fts_ ]]; then
            continue
        fi

        # Try to get count from sqlite_stat1 first (fast)
        count=$(sqlite3 "$DB_PATH" "SELECT stat FROM sqlite_stat1 WHERE tbl='$table' LIMIT 1;" 2>/dev/null | cut -d' ' -f1)

        if [[ -z "$count" ]]; then
            # Fallback: Use MAX(rowid) for large tables, COUNT(*) for small
            count=$(sqlite3 "$DB_PATH" "SELECT COALESCE(MAX(rowid), 0) FROM \"$table\";" 2>/dev/null || echo "?")
        fi

        # Format large numbers
        if [[ "$count" =~ ^[0-9]+$ ]] && [[ "$count" -gt 1000000 ]]; then
            formatted=$(echo "$count" | awk '{printf "%\047d", $1}')
        elif [[ "$count" =~ ^[0-9]+$ ]]; then
            formatted=$(printf "%'d" "$count" 2>/dev/null || echo "$count")
        else
            formatted="$count"
        fi

        printf "%-40s %15s\n" "$table" "$formatted"
    done
    echo
}

show_indices() {
    echo -e "${CYAN}=== Indices ===${NC}"

    # Group by table
    sqlite3 "$DB_PATH" "
        SELECT
            tbl_name,
            name,
            sql
        FROM sqlite_master
        WHERE type='index'
          AND sql IS NOT NULL
          AND name NOT LIKE 'sqlite_%'
        ORDER BY tbl_name, name;
    " | while IFS='|' read -r table idx sql; do
        echo -e "${GREEN}${table}${NC}.${YELLOW}${idx}${NC}"
        # Extract column from CREATE INDEX statement
        cols=$(echo "$sql" | grep -oP '\([^)]+\)' | tail -1)
        echo "    Columns: $cols"
    done
    echo
}

show_full_schema() {
    echo -e "${CYAN}=== Full Schema ===${NC}"
    sqlite3 "$DB_PATH" ".schema"
    echo
}

show_summary() {
    echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║           CROSSREF LOCAL DATABASE SUMMARY                  ║${NC}"
    echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    show_size
    show_tables

    echo -e "${CYAN}=== Key Indices ===${NC}"
    cat << 'EOF'
works:
  idx_doi_lookup           (doi)                    - exact DOI lookup
  idx_type                 (type)                   - filter by work type
  idx_container_title      (json $.container-title) - journal name lookup
  idx_issn                 (json $.ISSN[0])         - ISSN lookup
  idx_published_year       (json $.published.year)  - year filter
  idx_issn_year            (ISSN + year)            - compound filter

citations:
  idx_citations_citing     (citing_doi)             - outgoing citations
  idx_citations_cited_new  (cited_doi, citing_year) - incoming citations by year
  idx_citations_year_new   (citing_year)            - citations by year

journals_openalex:
  idx_openalex_issn_l      (issn_l)                 - primary ISSN lookup
  idx_openalex_name        (name)                   - journal name search
  idx_openalex_name_lower  (name_lower)             - case-insensitive search

EOF

    echo -e "${CYAN}=== Quick Reference ===${NC}"
    cat << 'EOF'
# Sample queries:
sqlite3 data/crossref.db "SELECT COUNT(*) FROM works;"
sqlite3 data/crossref.db "SELECT * FROM works WHERE doi='10.1038/nature12373';"
sqlite3 data/crossref.db "SELECT * FROM journals_openalex LIMIT 5;"

# Full-text search:
sqlite3 data/crossref.db "SELECT doi, title FROM works_fts WHERE works_fts MATCH 'neural network';"
EOF
}

# Main
check_db

case "${1:-}" in
    -h|--help)
        usage
        ;;
    -f|--full)
        show_full_schema
        ;;
    -t|--tables)
        show_tables
        ;;
    -i|--indices)
        show_indices
        ;;
    -s|--size)
        show_size
        ;;
    *)
        show_summary
        ;;
esac
