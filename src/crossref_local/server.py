#!/usr/bin/env python3
"""Backward compatibility: re-export from _server."""

from ._server import app, run_server, DEFAULT_PORT, DEFAULT_HOST

__all__ = ["app", "run_server", "DEFAULT_PORT", "DEFAULT_HOST"]

# EOF
