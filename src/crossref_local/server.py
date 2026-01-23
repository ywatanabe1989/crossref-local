"""FastAPI server for CrossRef Local with FTS5 search.

This module re-exports from the modular server package for backwards compatibility.

Usage:
    crossref-local api                    # Run on default port 31291
    crossref-local api --port 8080        # Custom port

    # Or directly:
    uvicorn crossref_local.server:app --host 0.0.0.0 --port 31291
"""

# Re-export from modular server package
from .server import app, run_server, DEFAULT_PORT, DEFAULT_HOST

__all__ = ["app", "run_server", "DEFAULT_PORT", "DEFAULT_HOST"]

if __name__ == "__main__":
    run_server()
