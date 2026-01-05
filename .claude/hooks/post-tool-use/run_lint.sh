#!/bin/bash
# -*- coding: utf-8 -*-
# Timestamp: "2025-12-24 04:52:51 (ywatanabe)"
# File: .//home/ywatanabe/.claude/hooks/run_lint.sh

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
# Description: Run linters with auto-fix after Write/Edit (PostToolUse hook)
#
# Supported languages:
#   - Python: ruff check --fix (or flake8 as fallback)
#   - TypeScript/JavaScript: eslint --fix
#   - Emacs Lisp: byte-compile
#   - Shell: shellcheck
#   - HTML: htmlhint
#
# Exit codes:
#   0 = Success
#   1 = Warning (Claude sees feedback but continues)
#   2 = Error (Claude must fix)

set -euo pipefail

# Add tool paths if they exist
NPM_GLOBAL_BIN="$HOME/.npm-global/bin"
LOCAL_BIN="$HOME/.local/bin"
GOPATH_BIN="$(go env GOPATH 2>/dev/null || true)/bin"

[ -d "$NPM_GLOBAL_BIN" ] && export PATH="$NPM_GLOBAL_BIN:$PATH"
[ -d "$LOCAL_BIN" ] && export PATH="$LOCAL_BIN:$PATH"
[ -d "$GOPATH_BIN" ] && export PATH="$GOPATH_BIN:$PATH"

# Read hook input JSON from stdin
INPUT=$(cat)

# Extract file_path from hook input
FILE_PATH=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('file_path', '') or '')
" 2>/dev/null || echo "")

# If no file path or file doesn't exist, nothing to lint
[ -n "$FILE_PATH" ] || exit 0
[ -f "$FILE_PATH" ] || exit 0

lint_python() {
    local file="$1"
    if command -v ruff &>/dev/null; then
        ruff check --fix "$file" 2>&1
        return $?
    elif command -v flake8 &>/dev/null; then
        flake8 "$file" 2>&1
        return $?
    fi
    return 0
}

lint_js_ts() {
    local file="$1"
    if command -v eslint &>/dev/null; then
        eslint --fix "$file" 2>&1
        return $?
    fi
    return 0
}

lint_elisp() {
    local file="$1"
    local exit_code=0
    # Check for common Emacs Lisp issues using emacs batch mode
    if command -v emacs &>/dev/null; then
        # Basic syntax check via byte-compilation
        emacs --batch \
            --eval "(setq byte-compile-error-on-warn t)" \
            --eval "(byte-compile-file \"$file\")" \
            2>&1
        exit_code=$?
        # Clean up .elc file
        rm -f "${file}c" 2>/dev/null || true
    fi
    return $exit_code
}

# lint_shell() {
#     local file="$1"
#     if command -v shellcheck &>/dev/null; then
#         shellcheck "$file" 2>&1
#         return $?
#     fi
#     return 0
# }

lint_shell() {
    local file="$1"
    if command -v shellcheck &>/dev/null; then
        shellcheck "$file" >&2  # Send to stderr so Claude sees it
        return $?
    fi
    return 0
}

lint_html() {
    local file="$1"
    if command -v htmlhint &>/dev/null; then
        htmlhint "$file" 2>&1
        return $?
    fi
    return 0
}

# Lint based on file extension and exit with code 2 on errors
case "$FILE_PATH" in
*.py)
    lint_python "$FILE_PATH" || exit 2
    ;;
*.ts | *.tsx | *.js | *.jsx)
    lint_js_ts "$FILE_PATH" || exit 2
    ;;
*.el)
    lint_elisp "$FILE_PATH" || exit 2
    ;;
*.sh | *.src | *.bash)
    lint_shell "$FILE_PATH" || exit 2
    ;;
*.html | *.htm)
    lint_html "$FILE_PATH" || exit 2
    ;;
esac

exit 0

# EOF