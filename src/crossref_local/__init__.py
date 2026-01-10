"""
crossref_local - Local CrossRef database with full-text search.

A Python package for querying a local mirror of the CrossRef database
with 167M+ scholarly works, full-text search, and impact factor calculation.

Basic usage:
    >>> from crossref_local import search, get
    >>> results = search("hippocampal sharp wave ripples")
    >>> print(f"Found {results.total} matches")
    >>> work = get("10.1126/science.aax0758")
    >>> print(work.title)

Configuration:
    >>> from crossref_local import configure
    >>> configure("/path/to/crossref.db")

    Or set CROSSREF_LOCAL_DB environment variable.
"""

__version__ = "0.1.0"

# Core API
from .api import (
    search,
    count,
    get,
    get_many,
    exists,
    configure,
    info,
)

# Models
from .models import Work, SearchResult

# Database utilities
from .db import Database, connection

# Configuration
from .config import Config

__all__ = [
    # Version
    "__version__",
    # Core API
    "search",
    "count",
    "get",
    "get_many",
    "exists",
    "configure",
    "info",
    # Models
    "Work",
    "SearchResult",
    # Database
    "Database",
    "connection",
    # Config
    "Config",
]
