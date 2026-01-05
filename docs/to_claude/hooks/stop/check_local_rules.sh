#!/bin/bash
# -*- coding: utf-8 -*-
# Timestamp: "2025-12-18 10:18:38 (ywatanabe)"
# File: .//home/ywatanabe/.claude/to_claude/hooks/check_local_rules.sh

ORIG_DIR="$(pwd)"
THIS_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
LOG_PATH="$THIS_DIR/.$(basename $0).log"
echo > "$LOG_PATH"

GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

GRAY='\033[0;90m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo_info() { echo -e "${GRAY}INFO: $1${NC}"; }
echo_success() { echo -e "${GREEN}SUCC: $1${NC}"; }
echo_warning() { echo -e "${YELLOW}WARN: $1${NC}"; }
echo_error() { echo -e "${RED}ERRO: $1${NC}"; }
echo_header() { echo_info "=== $1 ==="; }
# ---------------------------------------
#!/usr/bin/env bash
# Description: Check local coding rules (Stop hook / final gate)
#
# Checks for:
#   - Forbidden tokens (TODO, FIXME, HACK in committed code)
#   - Debug statements left in code
#   - Other team-specific rules
#
# Exit codes:
#   0 = All rules pass
#   2 = Violations found (Claude must fix)

set -euo pipefail

# Configuration
FORBIDDEN_TOKENS=("FIXME" "HACK") #  "XXX"
# Note: TODO is allowed for tracking work, but FIXME/HACK are not

# Find project root
find_project_root() {
    local dir="$(pwd)"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ]; then
            echo "$dir"
            return
        fi
        dir="$(dirname "$dir")"
    done
    echo "$(pwd)"
}

PROJECT_ROOT=$(find_project_root)
cd "$PROJECT_ROOT" 2>/dev/null || true

# Get changed files (staged or modified)
get_changed_files() {
    if [ -d ".git" ]; then
        git diff --name-only --cached 2>/dev/null || true
        git diff --name-only 2>/dev/null || true
    fi
}

CHANGED_FILES=$(get_changed_files | sort -u)

# If no changed files, nothing to check
[ -n "$CHANGED_FILES" ] || exit 0

VIOLATIONS=0

# Check for forbidden tokens
for file in $CHANGED_FILES; do
    [ -f "$file" ] || continue

    for token in "${FORBIDDEN_TOKENS[@]}"; do
        if grep -qn "$token" "$file" 2>/dev/null; then
            echo "Forbidden token '$token' found in: $file" >&2
            grep -n "$token" "$file" >&2
            VIOLATIONS=$((VIOLATIONS + 1))
        fi
    done
done

# Check for debug statements in Python
for file in $CHANGED_FILES; do
    [ -f "$file" ] || continue

    case "$file" in
        *.py)
            # Check for pdb/ipdb/breakpoint
            if grep -qnE '(import\s+i?pdb|\.set_trace\(\)|breakpoint\(\))' "$file" 2>/dev/null; then
                echo "Debug statement found in: $file" >&2
                grep -nE '(import\s+i?pdb|\.set_trace\(\)|breakpoint\(\))' "$file" >&2
                VIOLATIONS=$((VIOLATIONS + 1))
            fi
            ;;
        *.ts|*.tsx|*.js|*.jsx)
            # Check for debugger statements
            if grep -qn 'debugger;' "$file" 2>/dev/null; then
                echo "Debugger statement found in: $file" >&2
                grep -n 'debugger;' "$file" >&2
                VIOLATIONS=$((VIOLATIONS + 1))
            fi
            ;;
    esac
done

# Report summary
if [ "$VIOLATIONS" -gt 0 ]; then
    echo "" >&2
    echo "Local rules check: $VIOLATIONS violation(s) found" >&2
    echo "Please fix these issues before proceeding." >&2
    exit 2
fi

exit 0

# EOF