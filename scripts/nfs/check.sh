#!/bin/bash
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-14"
# Author: ywatanabe
# File: scripts/nfs/check.sh
# Description: Quick NFS check for make status (returns status code)

# For make status integration - minimal output
if rpcinfo -p localhost 2>/dev/null | grep -q nfs; then
    echo "  ✓ NFS server running"
    grep -q crossref /etc/exports 2>/dev/null && echo "  ✓ Export configured" || echo "  ✗ Export NOT configured"
else
    echo "  ✗ NFS server NOT running"
    if [[ -f /usr/sbin/conf_tool ]]; then
        echo "    UGREEN: Enable NFS in web UI first, then: make nfs-setup"
    else
        echo "    Hint: Run 'make nfs-setup' to configure"
    fi
fi

# EOF
