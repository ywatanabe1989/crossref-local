#!/bin/bash
# -*- mode: sh -*-
# ============================================================================
# CrossRef Local - Overall status check
# ============================================================================
# Usage: status.sh [OPTIONS]
#
# Options:
#   -h, --help    Show this help message and exit
#   -q, --quiet   Minimal output (exit code only)
#   -j, --json    Output status as JSON
#
# Environment:
#   CROSSREF_LOCAL_DB    Path to database (default: ./data/crossref.db)
#
# Examples:
#   ./status.sh           # Full status report
#   ./status.sh --quiet   # Exit 0 if healthy, 1 if issues
#   ./status.sh --json    # JSON output for scripting
# ============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Argument parsing
# -----------------------------------------------------------------------------
show_help() {
    sed -n '3,/^# ====/p' "$0" | head -n -1 | cut -c3-
    exit 0
}

QUIET=false
JSON=false

while [[ $# -gt 0 ]]; do
    case $1 in
    -h | --help)
        show_help
        ;;
    -q | --quiet)
        QUIET=true
        shift
        ;;
    -j | --json)
        JSON=true
        shift
        ;;
    *)
        echo "Unknown option: $1" >&2
        echo "Use --help for usage information" >&2
        exit 1
        ;;
    esac
done

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DB_PATH="${CROSSREF_LOCAL_DB:-$PROJECT_ROOT/data/crossref.db}"

# Track overall health
HEALTH_OK=true

# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------
check_database() {
    if [ -f "$DB_PATH" ]; then
        return 0
    else
        HEALTH_OK=false
        return 1
    fi
}

get_db_size() {
    if [ -f "$DB_PATH" ]; then
        du -h "$DB_PATH" | cut -f1
    else
        echo "N/A"
    fi
}

get_work_count() {
    if [ -f "$DB_PATH" ]; then
        sqlite3 "$DB_PATH" "SELECT stat FROM sqlite_stat1 WHERE tbl='works' LIMIT 1;" 2>/dev/null | cut -d' ' -f1 || echo "?"
    else
        echo "?"
    fi
}

get_citation_count() {
    if [ -f "$DB_PATH" ]; then
        sqlite3 "$DB_PATH" "SELECT MAX(rowid) FROM citations;" 2>/dev/null || echo "?"
    else
        echo "?"
    fi
}

# -----------------------------------------------------------------------------
# JSON output
# -----------------------------------------------------------------------------
if $JSON; then
    DB_EXISTS=$(check_database && echo "true" || echo "false")
    DB_SIZE=$(get_db_size)
    WORKS=$(get_work_count)
    CITATIONS=$(get_citation_count)

    cat <<EOF
{
  "healthy": $([[ "$DB_EXISTS" == "true" ]] && echo "true" || echo "false"),
  "database": {
    "path": "$DB_PATH",
    "exists": $DB_EXISTS,
    "size": "$DB_SIZE"
  },
  "stats": {
    "works": "$WORKS",
    "citations": "$CITATIONS"
  }
}
EOF
    if [[ "$DB_EXISTS" == "true" ]]; then exit 0; else exit 1; fi
fi

# -----------------------------------------------------------------------------
# Quiet mode
# -----------------------------------------------------------------------------
if $QUIET; then
    check_database
    exit $?
fi

# -----------------------------------------------------------------------------
# Full status report
# -----------------------------------------------------------------------------
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           CROSSREF LOCAL - STATUS                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Database
echo "=== Database ==="
if check_database; then
    echo "  ✓ Database: $DB_PATH"
    echo "  Size: $(get_db_size)"
else
    echo "  ✗ Database NOT FOUND: $DB_PATH"
    echo "    Hint: Set CROSSREF_LOCAL_DB or check data symlink"
fi
echo ""

# MCP Server
echo "=== MCP Server ==="
"$SCRIPT_DIR/deployment/mcp/status.sh" 2>/dev/null || echo "  (MCP status script not available)"

# NFS Server
echo "=== NFS Server ==="
"$SCRIPT_DIR/nfs/check.sh" 2>/dev/null || echo "  (NFS check script not available)"
echo ""

# Running Processes
echo "=== Running Processes ==="
if pgrep -af "(rebuild_citations|build_fts|sqlite3.*crossref)" 2>/dev/null | head -5; then
    :
else
    echo "  No database processes running"
fi
echo ""

# Screen Sessions
echo "=== Screen Sessions ==="
if screen -ls 2>/dev/null | grep -E "(citations|fts|rebuild)"; then
    :
else
    echo "  No relevant screen sessions"
fi
echo ""

# Quick Stats
echo "=== Quick Stats ==="
if [ -f "$DB_PATH" ]; then
    echo "  Works:     $(get_work_count)"
    echo "  Citations: $(get_citation_count)"
else
    echo "  (database not available)"
fi
echo ""

# Help
echo "Commands:"
echo "  make db-info      - Database details"
echo "  make mcp-status   - MCP server details"
echo "  make nfs-status   - NFS server details"

# Exit with health status
$HEALTH_OK && exit 0 || exit 1
