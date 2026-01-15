#!/bin/bash
# -*- coding: utf-8 -*-
# File: scripts/deployment/build_apptainer.sh
# Description: Build Apptainer/Singularity container image for crossref-local

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DEFINITION_FILE="${PROJECT_ROOT}/containers/crossref_local.def"
IMAGE_NAME="${PROJECT_ROOT}/containers/crossref_local.sif"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Build Apptainer/Singularity container image for crossref-local.

OPTIONS:
    -d, --def FILE     Definition file (default: containers/crossref_local.def)
    -o, --output FILE  Output image path (default: containers/crossref_local.sif)
    -f, --force        Force rebuild even if image exists
    -h, --help         Show this help message

EXAMPLES:
    $(basename "$0")                    # Build with defaults
    $(basename "$0") --force            # Force rebuild
    $(basename "$0") -o custom.sif      # Custom output path

PREREQUISITES:
    Install Apptainer: ./scripts/deployment/install_apptainer.sh
EOF
}

detect_builder() {
    if command -v apptainer &>/dev/null; then
        echo "apptainer"
    elif command -v singularity &>/dev/null; then
        echo "singularity"
    else
        echo -e "${RED}ERROR: Neither apptainer nor singularity found${NC}" >&2
        echo ""
        echo "Installation options:"
        echo "1. Install Apptainer:"
        echo "   ./scripts/deployment/install_apptainer.sh"
        echo ""
        echo "2. Or use Docker to build:"
        echo "   docker run --rm --privileged -v \$(pwd):/work -w /work \\"
        echo "     quay.io/singularity/singularity:v3.11.0 \\"
        echo "     build ${IMAGE_NAME} ${DEFINITION_FILE}"
        exit 1
    fi
}

# Parse arguments
FORCE=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d|--def) DEFINITION_FILE="$2"; shift 2 ;;
        -o|--output) IMAGE_NAME="$2"; shift 2 ;;
        -f|--force) FORCE=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; usage; exit 1 ;;
    esac
done

# Check definition file
if [[ ! -f "$DEFINITION_FILE" ]]; then
    echo -e "${RED}ERROR: Definition file not found: ${DEFINITION_FILE}${NC}" >&2
    exit 1
fi

# Check if image exists
if [[ -f "$IMAGE_NAME" ]] && [[ "$FORCE" != "1" ]]; then
    echo -e "${YELLOW}Image already exists: ${IMAGE_NAME}${NC}"
    echo "Use --force to rebuild"
    exit 0
fi

BUILDER=$(detect_builder)
echo -e "${GREEN}Building image with: ${BUILDER}${NC}"
echo "Definition: ${DEFINITION_FILE}"
echo "Output: ${IMAGE_NAME}"
echo ""

# Create output directory
mkdir -p "$(dirname "$IMAGE_NAME")"

# Build image
sudo ${BUILDER} build --force "${IMAGE_NAME}" "${DEFINITION_FILE}"

echo ""
echo -e "${GREEN}Build complete: ${IMAGE_NAME}${NC}"
echo ""
echo "Test the image:"
echo "  ${BUILDER} run ${IMAGE_NAME} crossref-local --help"
echo ""
echo "Run API server:"
echo "  ./scripts/deployment/run_apptainer.sh api"
