#!/bin/bash
# -*- mode: sh -*-
# CrossRef Local - Overall status check
# Called by: make status

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DB_PATH="${CROSSREF_LOCAL_DB:-$PROJECT_ROOT/data/crossref.db}"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           CROSSREF LOCAL - STATUS                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Database
echo "=== Database ==="
if [ -f "$DB_PATH" ]; then
    echo "  ✓ Database: $DB_PATH"
    echo "  Size: $(du -h "$DB_PATH" | cut -f1)"
else
    echo "  ✗ Database NOT FOUND: $DB_PATH"
    echo "    Hint: Set CROSSREF_LOCAL_DB or check data symlink"
fi
echo ""

# MCP Server
echo "=== MCP Server ==="
"$SCRIPT_DIR/deployment/mcp/status.sh"

# NFS Server
echo "=== NFS Server ==="
"$SCRIPT_DIR/nfs/check.sh" 2>/dev/null || echo "  (NFS check script not available)"
echo ""

# Running Processes
echo "=== Running Processes ==="
if ps aux | grep -E "(rebuild_citations|build_fts|sqlite3.*crossref)" | grep -v grep | head -5; then
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
    WORKS=$(sqlite3 "$DB_PATH" "SELECT stat FROM sqlite_stat1 WHERE tbl='works' LIMIT 1;" 2>/dev/null | cut -d' ' -f1 || echo "?")
    CITATIONS=$(sqlite3 "$DB_PATH" "SELECT MAX(rowid) FROM citations;" 2>/dev/null || echo "?")
    echo "  Works:     $WORKS"
    echo "  Citations: $CITATIONS"
else
    echo "  (database not available)"
fi
echo ""

# Help
echo "Commands:"
echo "  make db-info      - Database details"
echo "  make mcp-status   - MCP server details"
echo "  make nfs-status   - NFS server details"
