#!/usr/bin/env python3
"""Backward compatibility: re-export from _remote."""

from ._remote import RemoteClient, DEFAULT_API_URL, get_client, reset_client

__all__ = ["RemoteClient", "DEFAULT_API_URL", "get_client", "reset_client"]

# EOF
