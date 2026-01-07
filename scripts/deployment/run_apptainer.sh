#!/bin/bash
# Convenience wrapper for running Impact Factor Calculator with Apptainer

set -e

IMAGE="impact_factor.sif"
DATA_DIR="/mnt/nas_ug/crossref_local/data"
OUTPUT_DIR="./output"

# Check if image exists
if [ ! -f "${IMAGE}" ]; then
    echo "ERROR: Image not found: ${IMAGE}"
    echo "Build it first with: ./build_apptainer.sh"
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p "${OUTPUT_DIR}"

# Determine which tool to use
if command -v apptainer &> /dev/null; then
    RUNNER="apptainer"
elif command -v singularity &> /dev/null; then
    RUNNER="singularity"
else
    echo "ERROR: Neither apptainer nor singularity found"
    exit 1
fi

# Run container
${RUNNER} run \
    --bind "${DATA_DIR}:/data:ro" \
    --bind "${OUTPUT_DIR}:/output" \
    --pwd /app \
    "${IMAGE}" \
    "$@"
