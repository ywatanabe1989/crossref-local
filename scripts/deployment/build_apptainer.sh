#!/bin/bash
# -*- coding: utf-8 -*-
# Timestamp: "2025-10-12 07:05:40 (ywatanabe)"
# File: ./impact_factor/scripts/build_apptainer.sh

ORIG_DIR="$(pwd)"
THIS_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
LOG_PATH="$THIS_DIR/.$(basename $0).log"
echo > "$LOG_PATH"

BLACK='\033[0;30m'
LIGHT_GRAY='\033[0;37m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo_info() { echo -e "${LIGHT_GRAY}$1${NC}"; }
echo_success() { echo -e "${GREEN}$1${NC}"; }
echo_warning() { echo -e "${YELLOW}$1${NC}"; }
echo_error() { echo -e "${RED}$1${NC}"; }
# ---------------------------------------
# Build Apptainer/Singularity image for Impact Factor Calculator

set -e

DEFINITION_FILE="./containers/impact_factor.def"
IMAGE_NAME="./containers/impact_factor.sif"

echo "Building Apptainer image from ${DEFINITION_FILE}..."

# Check if apptainer or singularity is available
if command -v apptainer &> /dev/null; then
    BUILDER="apptainer"
elif command -v singularity &> /dev/null; then
    BUILDER="singularity"
else
    echo "ERROR: Neither apptainer nor singularity found in PATH"
    echo ""
    echo "Installation options:"
    echo "1. Install Apptainer:"
    echo "   wget https://github.com/apptainer/apptainer/releases/download/v1.2.5/apptainer_1.2.5_amd64.deb"
    echo "   sudo dpkg -i apptainer_1.2.5_amd64.deb"
    echo ""
    echo "2. Or use Docker to build:"
    echo "   docker run --rm --privileged -v \$(pwd):/work -w /work \\"
    echo "     quay.io/singularity/singularity:v3.11.0 \\"
    echo "     build ${IMAGE_NAME} ${DEFINITION_FILE}"
    exit 1
fi

echo "Using builder: ${BUILDER}"

# Build image
sudo ${BUILDER} build --force ${IMAGE_NAME} ${DEFINITION_FILE}

echo ""
echo "Build complete: ${IMAGE_NAME}"
echo ""
echo "Test the image:"
echo "  ${BUILDER} run --bind /mnt/nas_ug/crossref_local/data:/data:ro \\"
echo "    ${IMAGE_NAME} --help"
echo ""
echo "Run calculation:"
echo "  ${BUILDER} run --bind /mnt/nas_ug/crossref_local/data:/data:ro \\"
echo "    ${IMAGE_NAME} --journal 'Nature' --year 2023"

# EOF