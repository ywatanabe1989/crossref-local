#!/bin/bash
# -*- mode: sh -*-
# Check CrossRef MCP server status

SERVICE_NAME="crossref-mcp"

echo "=== MCP Server Status ==="

if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
    echo "  ✓ Service: RUNNING"

    # Get port from service
    PORT=$(systemctl show "$SERVICE_NAME" -p ExecStart 2>/dev/null | grep -oP '\-\-port \K\d+' || echo "8082")

    # Test endpoint
    if curl -s -o /dev/null -w '' "http://localhost:$PORT/mcp" 2>/dev/null; then
        echo "  ✓ Endpoint: http://localhost:$PORT/mcp (responding)"
    else
        echo "  ⚠ Endpoint: http://localhost:$PORT/mcp (not responding)"
    fi

    # Show uptime
    UPTIME=$(systemctl show "$SERVICE_NAME" --property=ActiveEnterTimestamp 2>/dev/null | cut -d= -f2)
    if [[ -n "$UPTIME" ]]; then
        echo "  Started: $UPTIME"
    fi
else
    if systemctl list-unit-files | grep -q "$SERVICE_NAME"; then
        echo "  ✗ Service: STOPPED (installed but not running)"
        echo ""
        echo "  Start with: sudo systemctl start $SERVICE_NAME"
    else
        echo "  ○ Service: NOT INSTALLED"
        echo ""
        echo "  Install with: make mcp-install"
    fi
fi

echo ""
