#!/usr/bin/env python3
"""Async API module for crossref_local.

Provides async versions of all API functions. Uses thread pool execution
with per-thread database connections for thread safety.

Usage:
    from crossref_local import aio

    async def main():
        results = await aio.search("machine learning")
        work = await aio.get("10.1038/nature12373")
        n = await aio.count("CRISPR")

    # Or import individual functions
    from crossref_local.aio import search, get, count

    # Concurrent operations
    counts = await aio.count_many(["CRISPR", "machine learning"])
"""

from ._aio import (
    SearchResult as _SearchResult,
    Work as _Work,
    count as _count,
    count_many as _count_many,
    exists as _exists,
    get as _get,
    get_many as _get_many,
    info as _info,
    search as _search,
    search_many as _search_many,
)

# Re-export with clean names
search = _search
count = _count
get = _get
get_many = _get_many
exists = _exists
info = _info
search_many = _search_many
count_many = _count_many
SearchResult = _SearchResult
Work = _Work

__all__ = [
    "search",
    "count",
    "get",
    "get_many",
    "exists",
    "info",
    "search_many",
    "count_many",
    "SearchResult",
    "Work",
]

# EOF
