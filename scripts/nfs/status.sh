#!/bin/bash
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-14"
# Author: ywatanabe
# File: scripts/nfs/status.sh
# Description: Show NFS server status and exports

set -euo pipefail

echo "=== NFS Server Status ==="
if systemctl is-active --quiet nfs-kernel-server 2>/dev/null; then
    echo "  ✓ NFS server is running"
else
    echo "  ✗ NFS server is NOT running"
    echo "    Hint: Run 'make nfs-setup' to configure"
fi

echo ""
echo "=== Current Exports ==="
showmount -e localhost 2>/dev/null || echo "  No exports (run: make nfs-setup)"

echo ""
echo "=== Client Mount Command ==="
IP=$(hostname -I | awk '{print $1}')
echo "  sudo mount -t nfs ${IP}:/path/to/crossref_local/data /mnt/crossref"

# EOF
