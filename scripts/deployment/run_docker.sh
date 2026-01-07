#!/bin/bash
# Convenience script to run impact factor calculations in Docker

set -e

IMAGE_NAME="impact-factor-calculator"
CONTAINER_NAME="impact-factor-calc"

# Build image if it doesn't exist
if [[ "$(docker images -q ${IMAGE_NAME} 2> /dev/null)" == "" ]]; then
    echo "Building Docker image..."
    docker build -t ${IMAGE_NAME} .
fi

# Run calculation
docker run --rm \
    -v /mnt/nas_ug/crossref_local/data:/data:ro \
    -v $(pwd)/output:/output \
    ${IMAGE_NAME} \
    python calculate_if.py "$@"
