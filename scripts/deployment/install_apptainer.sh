#!/bin/bash
# -*- coding: utf-8 -*-
# File: scripts/deployment/install_apptainer.sh
# Description: Install Apptainer container runtime

set -euo pipefail

VERSION="${APPTAINER_VERSION:-1.3.0}"
DEB_FILE="apptainer_${VERSION}_amd64.deb"
DEB_URL="https://github.com/apptainer/apptainer/releases/download/v${VERSION}/${DEB_FILE}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
    cat << EOF
Usage: $(basename "$0") [OPTIONS]

Install Apptainer container runtime for running crossref-local containers.

OPTIONS:
    -v, --version VER  Apptainer version to install (default: ${VERSION})
    -f, --force        Force reinstall even if already installed
    -h, --help         Show this help message

EXAMPLES:
    $(basename "$0")                    # Install default version
    $(basename "$0") -v 1.2.5           # Install specific version
    $(basename "$0") --force            # Force reinstall

NOTE:
    Requires sudo privileges for installation.
EOF
}

# Parse arguments
FORCE=0
while [[ $# -gt 0 ]]; do
    case "$1" in
        -v|--version) VERSION="$2"; shift 2 ;;
        -f|--force) FORCE=1; shift ;;
        -h|--help) usage; exit 0 ;;
        *) echo -e "${RED}Unknown option: $1${NC}"; usage; exit 1 ;;
    esac
done

# Update URL with possibly new version
DEB_FILE="apptainer_${VERSION}_amd64.deb"
DEB_URL="https://github.com/apptainer/apptainer/releases/download/v${VERSION}/${DEB_FILE}"

echo -e "${GREEN}=========================================="
echo "Apptainer Installation Script"
echo -e "==========================================${NC}"
echo ""
echo "Installing Apptainer ${VERSION}"
echo ""

# Check if already installed
if command -v apptainer &>/dev/null && [[ "$FORCE" != "1" ]]; then
    CURRENT_VERSION=$(apptainer --version | awk '{print $3}')
    echo -e "${YELLOW}Apptainer is already installed: ${CURRENT_VERSION}${NC}"
    echo "Use --force to reinstall"
    exit 0
fi

# Check for sudo
if ! command -v sudo &>/dev/null; then
    echo -e "${RED}ERROR: sudo is required for installation${NC}" >&2
    exit 1
fi

# Download .deb file
echo "Downloading Apptainer ${VERSION}..."
cd /tmp
wget -q --show-progress "${DEB_URL}"

# Install
echo ""
echo "Installing Apptainer..."
sudo dpkg -i "${DEB_FILE}"

# Fix dependencies if needed
echo ""
echo "Fixing dependencies..."
sudo apt-get install -f -y

# Cleanup
rm -f "${DEB_FILE}"

# Verify installation
echo ""
echo -e "${GREEN}=========================================="
echo "Installation complete!"
echo -e "==========================================${NC}"
apptainer --version

echo ""
echo "Test your installation:"
echo "  apptainer run library://alpine cat /etc/alpine-release"
echo ""
echo "Build crossref-local image:"
echo "  ./scripts/deployment/build_apptainer.sh"
