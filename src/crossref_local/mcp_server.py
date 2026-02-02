#!/usr/bin/env python3
"""Backward compatibility: re-export from _cli.mcp_server."""

from ._cli.mcp_server import mcp, run_server, main

__all__ = ["mcp", "run_server", "main"]

# EOF
