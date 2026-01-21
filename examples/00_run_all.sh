#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# Timestamp: 2026-01-22
# File: examples/00_run_all.sh
# Run all crossref-local examples

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    cat << EOF
Usage: ${0##*/} [OPTIONS]

Run all crossref-local examples.

Options:
    -h, --help      Show this help message
    -n, --dry-run   Show what would be run without executing
    -v, --verbose   Enable verbose output

Examples:
    ${0##*/}            # Run all examples
    ${0##*/} -n         # Dry run
    ${0##*/} -v         # Verbose mode

EOF
}

DRY_RUN=0
VERBOSE=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        -n|--dry-run)
            DRY_RUN=1
            shift
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 1
            ;;
    esac
done

run_cmd() {
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "[DRY-RUN] $*"
    else
        if [[ $VERBOSE -eq 1 ]]; then
            echo "[RUN] $*"
        fi
        "$@"
    fi
}

echo "=== CrossRef Local Examples ==="
echo

# 01: Quickstart
echo "--- 01_quickstart.py ---"
run_cmd python "$SCRIPT_DIR/01_quickstart.py"
echo

# 02: Citation Network
echo "--- 02_citation_network ---"
if [[ -f "$SCRIPT_DIR/02_citation_network/run.py" ]]; then
    run_cmd python "$SCRIPT_DIR/02_citation_network/run.py"
elif [[ -f "$SCRIPT_DIR/02_citation_network/main.py" ]]; then
    run_cmd python "$SCRIPT_DIR/02_citation_network/main.py"
else
    echo "  See 02_citation_network/ for citation network examples"
fi
echo

# 03: Impact Factor
echo "--- 03_impact_factor ---"
if [[ -f "$SCRIPT_DIR/03_impact_factor/run.py" ]]; then
    run_cmd python "$SCRIPT_DIR/03_impact_factor/run.py"
elif [[ -f "$SCRIPT_DIR/03_impact_factor/main.py" ]]; then
    run_cmd python "$SCRIPT_DIR/03_impact_factor/main.py"
else
    echo "  See 03_impact_factor/ for impact factor examples"
fi
echo

echo "=== Done ==="
