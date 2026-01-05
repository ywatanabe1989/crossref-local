#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# Timestamp: "2025-12-18 (ywatanabe)"
# File: ~/.claude/to_claude/hooks/run_tests.sh
# Description: Run corresponding test for edited file (PostToolUse hook)
#
# BEHAVIOR:
#   - Finds test file by basename: foo.py → test_foo.py, Bar.ts → Bar.test.ts
#   - FAILS if no corresponding test file exists (Claude must create it)
#   - FAILS if test execution fails (Claude must fix it)
#   - Respects .gitignore via git ls-files
#
# Exit codes: 0 = passed, 2 = failed (no test or test failed)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# =============================================================================
# SKIP CONFIGURATION
# =============================================================================
# Directories to skip
SKIP_DIRS=(".git" ".dev" ".old" "node_modules" "__pycache__" "migrations"
    "static" "templates" "dist" "build" ".venv" "venv")

# File patterns to skip
SKIP_FILES=("__init__.py" "apps.py" "admin.py" "urls.py" "conftest.py"
    "setup.py" "manage.py" "index.ts" "types.ts" "vite.config.ts"
    "vitest.config.ts" "test_*.py" "*_test.py" "*.test.ts" "*.spec.ts")

# Extensions to skip
SKIP_EXTENSIONS=(".md" ".rst" ".txt" ".json" ".yaml" ".yml" ".toml" ".ini"
    ".css" ".scss" ".html" ".svg" ".png" ".jpg" ".gif" ".ico"
    ".d.ts" ".lock" ".cfg" ".conf")

# Load project-specific config if exists
[ -f "$SCRIPT_DIR/run_tests.conf" ] && source "$SCRIPT_DIR/run_tests.conf"

# =============================================================================
# COLORS & INPUT
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('file_path', '') or '')" 2>/dev/null || echo "")

[ -z "$FILE_PATH" ] && exit 0
[ -f "$FILE_PATH" ] || exit 0

# =============================================================================
# HELPERS
# =============================================================================
find_project_root() {
    local dir
    dir=$(dirname "$1")
    while [ "$dir" != "/" ]; do
        [ -d "$dir/.git" ] && echo "$dir" && return
        dir=$(dirname "$dir")
    done
}

in_skip_dir() {
    for dir in "${SKIP_DIRS[@]}"; do
        [[ "$1" == *"/$dir/"* || "$1" == *"/$dir" ]] && return 0
    done
    return 1
}

is_skip_file() {
    for pattern in "${SKIP_FILES[@]}"; do
        case "$1" in $pattern) return 0 ;; esac
    done
    return 1
}

is_skip_ext() {
    for ext in "${SKIP_EXTENSIONS[@]}"; do
        [[ "$1" == *"$ext" ]] && return 0
    done
    return 1
}

# =============================================================================
# SKIP CHECKS
# =============================================================================
FILENAME=$(basename "$FILE_PATH")
in_skip_dir "$FILE_PATH" && exit 0
is_skip_file "$FILENAME" && exit 0
is_skip_ext "$FILENAME" && exit 0

# Only process testable source files
case "$FILENAME" in *.py | *.ts | *.tsx | *.el) ;; *) exit 0 ;; esac

# =============================================================================
# FIND PROJECT & TEST FILE
# =============================================================================
PROJECT_ROOT=$(find_project_root "$FILE_PATH")
[ -z "$PROJECT_ROOT" ] && exit 0
cd "$PROJECT_ROOT"
[ ! -d "tests" ] && exit 0

# Use git ls-files to respect .gitignore
find_test_file() {
    local basename="${1%.*}"
    local ext="${1##*.}"
    case "$ext" in
    py) git ls-files "tests/**/test_${basename}.py" 2>/dev/null | head -1 ;;
    ts | tsx) git ls-files "tests/**/${basename}.test.ts" "tests/**/${basename}.spec.ts" 2>/dev/null | head -1 ;;
    el) git ls-files "tests/**/test-${basename}.el" "tests/**/${basename}-test.el" 2>/dev/null | head -1 ;;
    esac
}

TEST_FILE=$(find_test_file "$FILENAME")

# Fallback to find if git ls-files returns empty (untracked test files)
if [ -z "$TEST_FILE" ]; then
    basename_no_ext="${FILENAME%.*}"
    ext="${FILENAME##*.}"
    case "$ext" in
    py) TEST_FILE=$(find tests/ -name "test_${basename_no_ext}.py" -not -path "*/.old*" 2>/dev/null | head -1) ;;
    ts | tsx) TEST_FILE=$(find tests/ \( -name "${basename_no_ext}.test.ts" -o -name "${basename_no_ext}.spec.ts" \) -not -path "*/.old*" 2>/dev/null | head -1) ;;
    el) TEST_FILE=$(find tests/ \( -name "test-${basename_no_ext}.el" -o -name "${basename_no_ext}-test.el" \) -not -path "*/.old*" 2>/dev/null | head -1) ;;
    esac
fi

# =============================================================================
# NO TEST FILE → FAIL
# =============================================================================
if [ -z "$TEST_FILE" ]; then
    local_path="${FILE_PATH#$PROJECT_ROOT/}"
    basename_no_ext="${FILENAME%.*}"
    ext="${FILENAME##*.}"
    echo "" >&2
    echo -e "${RED}❌ No test file for: $local_path${NC}" >&2
    case "$ext" in
    py) echo -e "${YELLOW}   Expected: tests/**/test_${basename_no_ext}.py${NC}" >&2 ;;
    ts | tsx) echo -e "${YELLOW}   Expected: tests/**/${basename_no_ext}.test.ts${NC}" >&2 ;;
    el) echo -e "${YELLOW}   Expected: tests/**/test-${basename_no_ext}.el${NC}" >&2 ;;
    esac
    echo "" >&2
    exit 2
fi

# =============================================================================
# RUN TESTS
# =============================================================================
echo -e "${CYAN}🧪 Running: $TEST_FILE${NC}" >&2

case "$TEST_FILE" in
*.py)
    if command -v pytest &>/dev/null; then
        pytest "$TEST_FILE" -q --tb=short 2>&1 || exit 2
    else
        python3 -m pytest "$TEST_FILE" -q --tb=short 2>&1 || exit 2
    fi
    ;;
*.ts)
    if command -v npx &>/dev/null; then
        npx vitest run "$TEST_FILE" --reporter=verbose 2>&1 || exit 2
    else
        npm test -- --run "$TEST_FILE" 2>&1 || exit 2
    fi
    ;;
*.el)
    emacs --batch --eval "(require 'ert)" --load "$TEST_FILE" \
        --eval "(ert-run-tests-batch-and-exit)" 2>&1 || exit 2
    ;;
esac

echo -e "${GREEN}✅ Tests passed${NC}" >&2
exit 0
