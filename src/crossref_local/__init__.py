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

Local mode (direct database access):
    >>> from crossref_local import configure
    >>> configure("/path/to/crossref.db")
    Or set CROSSREF_LOCAL_DB environment variable.

Remote mode (API access via HTTP):
    >>> from crossref_local import configure_remote
    >>> configure_remote("http://localhost:3333")
    Or set CROSSREF_LOCAL_API environment variable.

    Typical setup with SSH tunnel:
    $ ssh -L 3333:127.0.0.1:3333 nas  # In terminal
    >>> configure_remote()  # Uses default localhost:3333
"""

__version__ = "0.3.0"

# Core API
from .api import (
    search,
    count,
    get,
    get_many,
    exists,
    configure,
    configure_remote,
    get_mode,
    info,
)

# Remote client
from .remote import RemoteClient

# Models
from .models import Work, SearchResult

# Database utilities
from .db import Database, connection

# Configuration
from .config import Config

# Async API
from . import aio

# Citation network
from .citations import get_citing, get_cited, get_citation_count, CitationNetwork

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
    "configure_remote",
    "get_mode",
    "info",
    # Remote
    "RemoteClient",
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
    # Citations
    "get_citing",
    "get_cited",
    "get_citation_count",
    "CitationNetwork",
]
