#!/bin/bash
# -*- coding: utf-8 -*-
# Timestamp: "2025-12-24 07:09:46 (ywatanabe)"
# File: .//home/ywatanabe/.claude/hooks/post-tool-use/check_line_number_limit.sh

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

# Description: Claude Code hook to enforce file size limits

set -euo pipefail

# Thresholds (in lines)
THRESHOLD_TS=512
THRESHOLD_PY=512
THRESHOLD_CSS=512
THRESHOLD_HTML=1024
REFACTORING_MD="./REFACTORING.md"

# Read input from stdin
INPUT="$(cat)"

# Parse JSON using Python - outputs tab-separated values with line counts
# Capture output and exit code separately to properly handle parse failures
PARSED_OUTPUT=""
if ! PARSED_OUTPUT=$(echo "$INPUT" | python3 -c '
import json, sys
d = json.load(sys.stdin)
ti = d.get("tool_input", {}) or {}

def get_val(k):
    return (ti.get(k) or "").replace("\r\n", "\n")

file_path = get_val("file_path")
content = get_val("content")
old_string = get_val("old_string")
new_string = get_val("new_string")

# Count lines (add 1 if non-empty and no trailing newline for accurate count)
def count_lines(s):
    if not s:
        return 0
    return s.count("\n") + (1 if not s.endswith("\n") else 0)

content_lines = count_lines(content) if content else -1
old_lines = count_lines(old_string) if old_string else -1
new_lines = count_lines(new_string) if new_string else -1

print(f"{file_path}\t{content_lines}\t{old_lines}\t{new_lines}")
' 2>/dev/null); then
    # Failed to parse JSON - approve silently (non-monitored tool or malformed input)
    exit 0
fi

read -r FILE_PATH CONTENT_LINES OLD_LINES NEW_LINES <<<"$PARSED_OUTPUT"

# Exit if no file path (non-file operation or unsupported tool)
[ -n "$FILE_PATH" ] || exit 0

# Determine threshold based on extension
ext="${FILE_PATH##*.}"
case "$ext" in
py | el | sh | src) THRESHOLD="$THRESHOLD_PY" ;;
ts | tsx | js | jsx) THRESHOLD="$THRESHOLD_TS" ;;
css) THRESHOLD="$THRESHOLD_CSS" ;;
html | htm) THRESHOLD="$THRESHOLD_HTML" ;;
*) exit 0 ;;
esac

# Get current file line count
CURRENT=0
if [ -f "$FILE_PATH" ]; then
    CURRENT="$(wc -l <"$FILE_PATH" | tr -d ' ')"
fi

# Calculate proposed line count
if [ "$CONTENT_LINES" -ge 0 ]; then
    # Write operation: content specifies full file
    PROPOSED="$CONTENT_LINES"
elif [ "$OLD_LINES" -ge 0 ]; then
    # Edit operation: calculate delta
    PROPOSED=$((CURRENT - OLD_LINES + NEW_LINES))
    [ "$PROPOSED" -lt 0 ] && PROPOSED=0
else
    PROPOSED="$CURRENT"
fi

# Allow incremental reduction if currently over limit and edit shrinks it
if [ "$CURRENT" -gt "$THRESHOLD" ] && [ "$PROPOSED" -lt "$CURRENT" ]; then
    exit 0
fi

# Block any change that leaves file above threshold
if [ "$PROPOSED" -gt "$THRESHOLD" ]; then
    {
        echo "File size violation: $FILE_PATH"
        echo "  Lines: $PROPOSED (max: $THRESHOLD for .$ext)"
        echo ""
        echo "Rules:"
        echo "  - PY/SH/EL: max $THRESHOLD_PY lines"
        echo "  - TS/JS:    max $THRESHOLD_TS lines"
        echo "  - CSS:      max $THRESHOLD_CSS lines"
        echo "  - HTML:     max $THRESHOLD_HTML lines"
        echo ""
        echo "Action required:"
        echo "  1.  Document context in $REFACTORING_MD"
        echo "  2.  Refactor (split modules, keep orchestrator thin)"
        echo "  2.1 Following convensions in the project"
        echo "  2.2 Use subdirectories wisely"
        echo "  3.  Delete $REFACTORING_MD after completion"
    } >&2
    exit 2
fi

exit 0

# EOF