"""
crossref_local - Local CrossRef database with full-text search.

A Python package for querying a local mirror of the CrossRef database
with 167M+ scholarly works, full-text search, and impact factor calculation.

Sync usage:
    >>> from crossref_local import search, get
    >>> results = search("hippocampal sharp wave ripples")
    >>> work = get("10.1126/science.aax0758")

Async usage:
    >>> from crossref_local import aio
    >>> results = await aio.search("machine learning")
    >>> counts = await aio.count_many(["CRISPR", "neural network"])

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

# Async API
from . import aio

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
    # Async
    "aio",
]
