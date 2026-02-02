#!/usr/bin/env python3
"""Backward compatibility: re-export from _cli."""

from ._cli import cli, main

__all__ = ["cli", "main"]

# EOF
