#!/bin/bash
# CrossRef Local - CLI Demo
#
# Demonstrates all CLI commands with real output.
#
# Usage:
#     bash examples/demo_cli.sh
#     bash examples/demo_cli.sh 2>&1 | tee demo_cli.log

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CROSSREF LOCAL - CLI DEMO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# -----------------------------------------------------------------------------
echo "─────────────────────────────────────────────────────────────────────"
echo "  1. Setup Check"
echo "─────────────────────────────────────────────────────────────────────"
echo
echo "$ crossref-local setup"
crossref-local setup
echo

# -----------------------------------------------------------------------------
echo "─────────────────────────────────────────────────────────────────────"
echo "  2. Full-Text Search"
echo "─────────────────────────────────────────────────────────────────────"
echo
echo "$ crossref-local search 'hippocampal sharp wave ripples' -n 3"
crossref-local search "hippocampal sharp wave ripples" -n 3
echo

# -----------------------------------------------------------------------------
echo "─────────────────────────────────────────────────────────────────────"
echo "  3. Get by DOI"
echo "─────────────────────────────────────────────────────────────────────"
echo
echo "$ crossref-local get 10.1038/nature12373"
crossref-local get 10.1038/nature12373
echo

# -----------------------------------------------------------------------------
echo "─────────────────────────────────────────────────────────────────────"
echo "  4. Count Matches"
echo "─────────────────────────────────────────────────────────────────────"
echo
echo "$ crossref-local count 'machine learning'"
crossref-local count "machine learning"
echo

# -----------------------------------------------------------------------------
echo "─────────────────────────────────────────────────────────────────────"
echo "  5. Database Info"
echo "─────────────────────────────────────────────────────────────────────"
echo
echo "$ crossref-local info"
crossref-local info
echo

# -----------------------------------------------------------------------------
echo "─────────────────────────────────────────────────────────────────────"
echo "  6. Impact Factor"
echo "─────────────────────────────────────────────────────────────────────"
echo
echo "$ crossref-local impact-factor Nature -y 2023"
crossref-local impact-factor Nature -y 2023 || echo "(Impact factor calculation may require citations table)"
echo

# -----------------------------------------------------------------------------
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CLI DEMO COMPLETE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo
echo "For more options: crossref-local --help"
echo
