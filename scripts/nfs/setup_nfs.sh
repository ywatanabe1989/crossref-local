#!/bin/bash
# -*- mode: sh -*-
# NFS Setup Script for CrossRef Local Database
#
# Usage:
#   ./scripts/nfs/setup_nfs.sh
#   make nfs-setup
#
# Prerequisites:
#   - .env file with SUDO_PASSWORD set
#   - NFS enabled in UGREEN web UI (if running on UGREEN NAS)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_hint() { echo -e "       ${YELLOW}Hint:${NC} $1"; }

# Load .env file
if [[ ! -f "$ENV_FILE" ]]; then
    log_error ".env file not found"
    log_hint "Copy .env.example to .env and set SUDO_PASSWORD"
    log_hint "  cp .env.example .env && echo 'SUDO_PASSWORD=yourpassword' >> .env"
    exit 1
fi

# Source .env safely (handle special characters)
set -a
source "$ENV_FILE"
set +a

if [[ -z "${SUDO_PASSWORD:-}" ]]; then
    log_error "SUDO_PASSWORD not set in .env"
    log_hint "Add to .env: SUDO_PASSWORD=yourpassword"
    exit 1
fi

# Helper function to run sudo commands with password from env
run_sudo() {
    printf '%s\n' "$SUDO_PASSWORD" | sudo -S "$@" 2>/dev/null
}

# Check if nfs-kernel-server is installed
if ! dpkg -l nfs-kernel-server 2>/dev/null | grep -q "^ii"; then
    log_error "nfs-kernel-server not installed"
    log_hint "Install with: sudo apt install nfs-kernel-server"
    exit 1
fi

# NFS Export configuration
DATA_PATH="$PROJECT_ROOT/data"
EXPORT_LINE="$DATA_PATH 192.168.0.0/16(ro,sync,no_subtree_check,all_squash,anonuid=1000,anongid=1000) 169.254.0.0/16(ro,sync,no_subtree_check,all_squash,anonuid=1000,anongid=1000)"

log_info "Starting NFS setup for CrossRef Local..."
log_info "Data path: $DATA_PATH"

# Verify data path exists
if [[ ! -d "$DATA_PATH" ]]; then
    log_error "Data directory not found: $DATA_PATH"
    log_hint "Create symlink or directory for database"
    exit 1
fi

# Detect UGREEN NAS
IS_UGREEN=false
if [[ -f /usr/sbin/conf_tool ]]; then
    IS_UGREEN=true
    log_info "Detected UGREEN NAS environment"
fi

# Step 1: Configure exports
log_info "Step 1/3: Configuring NFS exports..."
EXPORTS_CONTENT=$(run_sudo cat /etc/exports 2>/dev/null || echo "")

if echo "$EXPORTS_CONTENT" | grep -q "$DATA_PATH"; then
    log_warn "Export already exists for $DATA_PATH"
else
    if printf '%s\n' "$SUDO_PASSWORD" | sudo -S tee -a /etc/exports > /dev/null <<< "$EXPORT_LINE"; then
        log_info "Added export to /etc/exports"
    else
        log_error "Failed to add export"
        log_hint "Manually add to /etc/exports:"
        echo "  $EXPORT_LINE"
        exit 1
    fi
fi

# Step 2: Try to start NFS server
log_info "Step 2/3: Starting NFS server..."

if $IS_UGREEN; then
    # UGREEN NAS requires enabling NFS through web UI
    if ! run_sudo systemctl start nfs-kernel-server 2>&1 | grep -q ""; then
        log_warn "UGREEN NAS detected - NFS may need to be enabled via web UI"
        log_hint "Go to UGREEN web interface -> File Services -> NFS -> Enable"
        log_hint "After enabling in web UI, run this script again"
    fi
else
    run_sudo systemctl enable nfs-kernel-server || true
    run_sudo systemctl start nfs-kernel-server || true
fi

# Step 3: Apply exports
log_info "Step 3/3: Applying NFS configuration..."
run_sudo exportfs -ra || true

# Check actual NFS status
echo ""
log_info "=== Status Check ==="

NFS_RUNNING=false
if rpcinfo -p localhost 2>/dev/null | grep -q nfs; then
    NFS_RUNNING=true
    log_info "✓ NFS service is running"
else
    log_warn "✗ NFS service is NOT running"
fi

# Show configured exports
echo ""
log_info "Configured exports in /etc/exports:"
run_sudo exportfs -v 2>/dev/null | head -10 || echo "  (unable to read exports)"

# Final guidance
echo ""
if $NFS_RUNNING; then
    log_info "NFS setup complete!"
    echo ""
    echo "Remote machines can mount via:"
    IP_ADDR=$(hostname -I | awk '{print $1}')
    echo "  sudo mount -t nfs ${IP_ADDR}:${DATA_PATH} /mnt/crossref"
else
    if $IS_UGREEN; then
        log_error "NFS server not running"
        echo ""
        echo "UGREEN NAS requires NFS to be enabled via web interface:"
        echo "  1. Open UGREEN web UI (http://$(hostname -I | awk '{print $1}'):9999)"
        echo "  2. Go to: Settings -> File Services -> NFS"
        echo "  3. Enable NFS service"
        echo "  4. Run: make nfs-setup  (again)"
        echo ""
        echo "Exports are already configured in /etc/exports"
    else
        log_error "NFS server failed to start"
        log_hint "Check: journalctl -xeu nfs-kernel-server"
    fi
fi

echo ""
echo "Check status anytime with: make nfs-status"
