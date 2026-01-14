#!/bin/bash
# -*- coding: utf-8 -*-
# Time-stamp: "2026-01-14"
# Author: ywatanabe
# File: scripts/nfs/stop.sh
# Description: Stop NFS server

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    source "${PROJECT_ROOT}/.env"
    echo "${SUDO_PASSWORD}" | sudo -S systemctl stop nfs-kernel-server
    echo "NFS server stopped"
else
    echo "Error: .env file not found"
    echo "Hint: Create .env with SUDO_PASSWORD=yourpassword"
    exit 1
fi

# EOF
