"""
crossref_local - Local CrossRef database with full-text search.

A Python package for querying a local mirror of the CrossRef database
with 167M+ scholarly works, full-text search, and impact factor calculation.

Quick Start
-----------

Sync usage:
    >>> from crossref_local import search, get
    >>> results = search("hippocampal sharp wave ripples")
    >>> work = get("10.1126/science.aax0758")

Async usage:
    >>> from crossref_local import aio
    >>> results = await aio.search("machine learning")
    >>> counts = await aio.count_many(["CRISPR", "neural network"])

Configuration
-------------

DB mode (direct database access):
    >>> from crossref_local import configure
    >>> configure("/path/to/crossref.db")
    Or set CROSSREF_LOCAL_DB environment variable.

HTTP mode (API access via HTTP):
    >>> from crossref_local import configure_http
    >>> configure_http("http://localhost:8333")
    Or set CROSSREF_LOCAL_API_URL environment variable.

    Typical setup with SSH tunnel:
    $ ssh -L 8333:127.0.0.1:8333 your-server  # In terminal
    >>> configure_http()  # Uses default localhost:8333

Public API
----------

Functions:
    search(query, limit, offset) -> SearchResult
    count(query) -> int
    get(doi) -> Work | None
    get_many(dois) -> list[Work]
    exists(doi) -> bool
    enrich(results) -> SearchResult
    enrich_dois(dois) -> list[Work]
    configure(db_path) -> None
    configure_remote(api_url) -> None
    get_mode() -> str
    info() -> dict

Citation functions:
    get_citing(doi) -> list[str]
    get_cited(doi) -> list[str]
    get_citation_count(doi) -> int

Classes:
    Work - Scholarly work with title, authors, DOI, etc.
    SearchResult - Container for search results
    CitationNetwork - Citation graph builder and visualizer

Modules:
    aio - Async versions of all API functions
"""

__version__ = "0.3.1"

# Core API (public functions)
from .api import (
    search,
    count,
    get,
    get_many,
    exists,
    enrich,
    enrich_dois,
    configure,
    configure_http,
    configure_remote,  # Backward compatibility alias
    get_mode,
    info,
)

# Models (public classes)
from .models import Work, SearchResult

# Async API (public module)
from . import aio

# Citation network (public functions and classes)
from .citations import get_citing, get_cited, get_citation_count, CitationNetwork

# Cache module (public)
from . import cache


# Public API - what users should import
__all__ = [
    # Version
    "__version__",
    # Core search/retrieval
    "search",
    "count",
    "get",
    "get_many",
    "exists",
    # Enrichment (add citations/references to search results)
    "enrich",
    "enrich_dois",
    # Configuration
    "configure",
    "configure_http",
    "configure_remote",  # Backward compatibility alias
    "get_mode",
    "info",
    # Data models
    "Work",
    "SearchResult",
    # Async API
    "aio",
    # Cache module
    "cache",
    # Citation network
    "get_citing",
    "get_cited",
    "get_citation_count",
    "CitationNetwork",
]


# ============================================================================
# Advanced / Internal APIs (not in __all__, but importable if needed)
# ============================================================================
# These are exposed for advanced users but not part of the stable public API.
# Use at your own risk - they may change without notice.
#
# from crossref_local.db import Database, connection
# from crossref_local.config import Config
# from crossref_local.remote import RemoteClient
# from crossref_local.fts import search_dois
# ============================================================================
