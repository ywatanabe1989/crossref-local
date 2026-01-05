#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# Timestamp: "2025-12-18 (ywatanabe)"
# File: ~/.claude/to_claude/hooks/format_code.sh
# Description: Auto-format code after Write/Edit (PostToolUse hook)
#
# Supported languages:
#   - Python: ruff format (or black as fallback)
#   - TypeScript/JavaScript: prettier
#   - CSS: prettier
#   - Emacs Lisp: elinter
#   - Shell: shfmt
#   - HTML: prettier
#
# Exit codes:
#   0 = Success
#   1 = Warning (non-blocking)

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

# If no file path or file doesn't exist, nothing to format
[ -n "$FILE_PATH" ] || exit 0
[ -f "$FILE_PATH" ] || exit 0

format_python() {
    local file="$1"
    if command -v ruff &>/dev/null; then
        ruff format "$file" 2>/dev/null || true
    elif command -v black &>/dev/null; then
        black "$file" 2>/dev/null || true
    fi
}

format_js_ts() {
    local file="$1"
    if command -v prettier &>/dev/null; then
        prettier --write "$file" 2>/dev/null || true
    fi
}

format_elisp() {
    local file="$1"
    local elinter_path="$HOME/.emacs.d/lisp/elinter"
    if command -v emacs &>/dev/null && [ -d "$elinter_path" ]; then
        # Use elinter for formatting
        emacs --batch \
            --eval "(add-to-list 'load-path \"$elinter_path\")" \
            --eval "(require 'elinter)" \
            --eval "(find-file \"$file\")" \
            --eval "(elinter-lint-buffer)" \
            --eval "(save-buffer)" \
            2>/dev/null || true
    elif command -v emacs &>/dev/null; then
        # Fallback to basic indent
        emacs --batch "$file" \
            --eval "(indent-region (point-min) (point-max))" \
            --eval "(save-buffer)" \
            2>/dev/null || true
    fi
}

format_shell() {
    local file="$1"
    if command -v shfmt &>/dev/null; then
        shfmt -w -i 4 "$file" 2>/dev/null || true
    fi
}

format_html() {
    local file="$1"
    if command -v prettier &>/dev/null; then
        prettier --write "$file" 2>/dev/null || true
    fi
}

# Format based on file extension
case "$FILE_PATH" in
*.py)
    format_python "$FILE_PATH"
    ;;
*.ts | *.tsx | *.js | *.jsx)
    format_js_ts "$FILE_PATH"
    ;;
*.css)
    format_js_ts "$FILE_PATH"
    ;;
*.el)
    format_elisp "$FILE_PATH"
    ;;
*.sh | *.src | *.bash)
    format_shell "$FILE_PATH"
    ;;
*.html | *.htm)
    format_html "$FILE_PATH"
    ;;
esac

exit 0
