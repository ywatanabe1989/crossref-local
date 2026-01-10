#!/bin/bash
# -*- coding: utf-8 -*-
# File: ./tests/sync_tests_with_source.sh

# =============================================================================
# Test Synchronization Script for crossref_local
# =============================================================================
#
# PURPOSE:
#   Synchronizes test file structure with source code structure, ensuring
#   every source file has a corresponding test file with embedded source
#   code for reference.
#
# USAGE:
#   ./sync_tests_with_source.sh          # Dry run - report stale files
#   ./sync_tests_with_source.sh -m       # Move stale files to .old/
#
# =============================================================================

set -e

ORIG_DIR="$(pwd)"
THIS_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
ROOT_DIR="$(realpath $THIS_DIR/..)"

# Color scheme
GRAY='\033[0;90m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo_info() { echo -e "${GRAY}INFO: $1${NC}"; }
echo_success() { echo -e "${GREEN}SUCC: $1${NC}"; }
echo_warning() { echo -e "${YELLOW}WARN: $1${NC}"; }
echo_error() { echo -e "${RED}ERRO: $1${NC}"; }
echo_header() { echo_info "=== $1 ==="; }

# Default Values
DO_MOVE=false
SRC_DIR="$ROOT_DIR/src/crossref_local"
TESTS_DIR="$ROOT_DIR/tests/crossref_local"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -m|--move) DO_MOVE=true; shift ;;
        -h|--help)
            echo "Usage: $0 [-m|--move]"
            echo "  -m  Move stale test files to .old/"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

get_pytest_guard() {
    echo ''
    echo 'if __name__ == "__main__":'
    echo '    import os'
    echo '    import pytest'
    echo '    pytest.main([os.path.abspath(__file__)])'
}

get_source_code_block() {
    local src_file=$1
    echo ""
    echo "# --------------------------------------------------------------------------------"
    echo "# Start of Source Code from: $src_file"
    echo "# --------------------------------------------------------------------------------"
    sed 's/^/# /' "$src_file"
    echo ""
    echo "# --------------------------------------------------------------------------------"
    echo "# End of Source Code from: $src_file"
    echo "# --------------------------------------------------------------------------------"
}

process_file() {
    local src_file="$1"
    local src_base=$(basename "$src_file")

    # Skip __init__.py
    [[ "$src_base" == "__init__.py" ]] && return

    # Get relative path from SRC_DIR
    local rel="${src_file#$SRC_DIR/}"
    local rel_dir=$(dirname "$rel")
    local test_dir="$TESTS_DIR/$rel_dir"
    local test_file="$test_dir/test_$src_base"

    mkdir -p "$test_dir"

    if [ ! -f "$test_file" ]; then
        # Create new test file
        cat > "$test_file" << EOL
# Add your tests here

$(get_pytest_guard)
EOL
        get_source_code_block "$src_file" >> "$test_file"
        echo_success "Created: $test_file"
    else
        # Update existing - preserve test code
        local temp_file=$(mktemp)
        local test_code=""

        if grep -q "# Start of Source Code from:" "$test_file"; then
            test_code=$(sed -n '/# Start of Source Code from:/q;/if __name__ == "__main__":/q;p' "$test_file")
        else
            test_code=$(sed -n '/if __name__ == "__main__":/q;p' "$test_file")
        fi

        if [ -n "$test_code" ]; then
            echo "$test_code" > "$temp_file"
        else
            echo "# Add your tests here" > "$temp_file"
            echo "" >> "$temp_file"
        fi

        get_pytest_guard >> "$temp_file"
        get_source_code_block "$src_file" >> "$temp_file"
        mv "$temp_file" "$test_file"
        echo_info "Updated: $test_file"
    fi
}

main() {
    echo ""
    echo_header "Test Synchronization"
    echo ""
    echo_info "Source: $SRC_DIR"
    echo_info "Tests:  $TESTS_DIR"
    echo ""

    # Find all Python files
    find "$SRC_DIR" -name "*.py" -not -path "*__pycache__*" | while read -r src_file; do
        process_file "$src_file"
    done

    # Report stale tests
    echo ""
    echo_header "Checking for stale tests"
    find "$TESTS_DIR" -name "test_*.py" -not -path "*.old*" | while read -r test_file; do
        local test_base=$(basename "$test_file")
        local src_base="${test_base#test_}"
        local rel_dir=$(dirname "${test_file#$TESTS_DIR/}")
        local src_file="$SRC_DIR/$rel_dir/$src_base"

        if [ ! -f "$src_file" ]; then
            if [ "$DO_MOVE" = "true" ]; then
                local old_dir="$(dirname $test_file)/.old-$(date +%Y%m%d)"
                mkdir -p "$old_dir"
                mv "$test_file" "$old_dir/"
                echo_success "Moved stale: $test_file"
            else
                echo_warning "Stale: $test_file"
            fi
        fi
    done

    echo ""
    echo_success "Sync complete!"
    echo ""
}

main "$@"
cd "$ORIG_DIR"
