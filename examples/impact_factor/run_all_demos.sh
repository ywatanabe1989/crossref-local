#!/bin/bash
# -*- coding: utf-8 -*-
# Timestamp: "2026-01-07 22:48:54 (ywatanabe)"
# File: /home/ywatanabe/proj/crossref_local/examples/impact_factor/run_all_demos.sh
#
# Run all Impact Factor demos in sequence

ORIG_DIR="$(pwd)"
THIS_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
LOG_PATH="$THIS_DIR/$(basename $0).log"
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
echo_header() { echo -e "\n${GRAY}=== $1 ===${NC}"; }
# ---------------------------------------

cd "$THIS_DIR"

# Step 0: Basic IF calculation demo
echo_header "00: Calculate Impact Factor Demo"
python3 00_calculate_impact_factor.py --journal "Nature" --year 2023 2>&1 | tee -a "$LOG_PATH"
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo_success "00_calculate_impact_factor.py completed"
else
    echo_error "00_calculate_impact_factor.py failed"
fi

# Step 1: Compare with JCR
echo_header "01: Compare with JCR Official Values"
python3 01_compare_jcr.py --category all 2>&1 | tee -a "$LOG_PATH"
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo_success "01_compare_jcr.py completed"
else
    echo_error "01_compare_jcr.py failed"
fi

# Step 2: Generate validation plot
echo_header "02: Generate Validation Plot"
python3 02_compare_jcr_plot.py 2>&1 | tee -a "$LOG_PATH"
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo_success "02_compare_jcr_plot.py completed"
else
    echo_error "02_compare_jcr_plot.py failed"
fi

echo_header "All demos completed"
echo_info "Log saved to: $LOG_PATH"
echo_info "Outputs:"
echo_info "  - 01_compare_jcr_out/"
echo_info "  - 02_compare_jcr_plot_out/"

cd "$ORIG_DIR"

# EOF