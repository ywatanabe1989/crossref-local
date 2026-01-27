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

echo "=== impact_factor/run_all_demos.sh ==="
cd impact_factor && ./run_all_demos.sh && cd ..
echo ""

echo "=== citation_network/01_generate_visualization.py ==="
python3 citation_network/01_generate_visualization.py
echo ""

echo "All examples completed successfully."
