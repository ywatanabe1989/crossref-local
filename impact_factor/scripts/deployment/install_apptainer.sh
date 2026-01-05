#!/bin/bash
# -*- coding: utf-8 -*-
# Timestamp: "2025-10-12 02:53:00 (ywatanabe)"
# File: /home/ywatanabe/.dotfiles/.bin/installers/install_apptainer.sh

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

VERSION="1.3.0"
DEB_FILE="apptainer_${VERSION}_amd64.deb"
DEB_URL="https://github.com/apptainer/apptainer/releases/download/v${VERSION}/${DEB_FILE}"

echo_info "=========================================="
echo_info "Apptainer Installation Script"
echo_info "=========================================="
echo_info ""
echo_info "Installing Apptainer ${VERSION}"
echo_info ""

# Check if already installed
if command -v apptainer &> /dev/null; then
    CURRENT_VERSION=$(apptainer --version | awk '{print $3}')
    echo_warning "Apptainer is already installed: ${CURRENT_VERSION}"
    read -p "Do you want to reinstall? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo_info "Installation cancelled."
        exit 0
    fi
fi

# Check for sudo
if ! command -v sudo &> /dev/null; then
    echo_error "ERROR: sudo is required for installation"
    exit 1
fi

# Download .deb file
echo_info "Downloading Apptainer ${VERSION}..."
cd /tmp
wget -q --show-progress "${DEB_URL}" 2>&1 | tee -a "$LOG_PATH"

# Install
echo_info ""
echo_info "Installing Apptainer..."
sudo dpkg -i "${DEB_FILE}" 2>&1 | tee -a "$LOG_PATH"

# Fix dependencies if needed
echo_info ""
echo_info "Fixing dependencies..."
sudo apt-get install -f -y 2>&1 | tee -a "$LOG_PATH"

# Cleanup
rm -f "${DEB_FILE}"

# Verify installation
echo_info ""
echo_success "=========================================="
echo_success "Installation complete!"
echo_success "=========================================="
apptainer --version

echo_info ""
echo_info "Test your installation:"
echo_info "  apptainer run library://alpine cat /etc/alpine-release"
echo_info ""
echo_info "Build impact factor calculator image:"
echo_info "  cd /mnt/nas_ug/crossref_local/impact_factor"
echo_info "  ./scripts/build_apptainer.sh"
echo_info ""
echo_success "Log saved to: $LOG_PATH"

# EOF
