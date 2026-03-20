#!/bin/bash
# -*- coding: utf-8 -*-
# Run all crossref-local examples
#
# Usage:
#   ./examples/00_run_all.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Running crossref-local examples..."
echo ""

echo "=== 01_quickstart.py ==="
python3 01_quickstart.py
echo ""

echo "=== 03_impact_factor/run_all_demos.sh ==="
cd 03_impact_factor && ./run_all_demos.sh && cd ..
echo ""

echo "=== 02_citation_network/01_generate_visualization.py ==="
python3 02_citation_network/01_generate_visualization.py
echo ""

echo "All examples completed successfully."
