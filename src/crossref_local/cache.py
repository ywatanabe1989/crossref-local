"""Cache module for crossref-local.

Provides disk-based caching of paper metadata to reduce context usage
and enable efficient re-querying with field filtering.

Architecture:
    1. FTS search -> DOIs (fast, minimal)
    2. Cache DOIs -> full metadata saved to disk
    3. Query cache -> filtered fields based on need

Usage:
    >>> from crossref_local import cache
    >>> # Create cache from search
    >>> cache.create("epilepsy", query="epilepsy seizure prediction", limit=100)
    >>> # Query with minimal fields
    >>> papers = cache.query("epilepsy", fields=["doi", "title", "year"])
    >>> # Get statistics
    >>> stats = cache.stats("epilepsy")
"""

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .api import get_many, search


def _get_cache_dir() -> Path:
    """Get cache directory, creating if needed."""
    cache_dir = Path(
        os.environ.get(
            "CROSSREF_LOCAL_CACHE_DIR", Path.home() / ".cache" / "crossref-local"
        )
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def _cache_path(name: str) -> Path:
    """Get path for a named cache."""
    return _get_cache_dir() / f"{name}.json"


def _meta_path(name: str) -> Path:
    """Get path for cache metadata."""
    return _get_cache_dir() / f"{name}.meta.json"


@dataclass
class CacheInfo:
    """Information about a cache."""

    name: str
    path: str
    size_bytes: int
    paper_count: int
    created_at: str
    query: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "path": self.path,
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_bytes / 1024 / 1024, 2),
            "paper_count": self.paper_count,
            "created_at": self.created_at,
            "query": self.query,
        }


def create(
    name: str,
    query: Optional[str] = None,
    dois: Optional[List[str]] = None,
    papers: Optional[List[Dict[str, Any]]] = None,
    limit: int = 1000,
    offset: int = 0,
) -> CacheInfo:
    """Create a cache from search query, DOI list, or pre-fetched papers.

    Args:
        name: Cache name (used as filename)
        query: FTS search query (if dois/papers not provided)
        dois: Explicit list of DOIs to cache
        papers: Pre-fetched paper dicts (skips API calls)
        limit: Max papers to fetch (for query mode)
        offset: Offset for pagination (for query mode)

    Returns:
        CacheInfo with cache details

    Example:
        >>> create("epilepsy", query="epilepsy seizure", limit=500)
        >>> create("my_papers", dois=["10.1038/nature12373", ...])
        >>> create("imported", papers=[{"doi": "...", "title": "..."}])
    """
    if papers is not None:
        # Use pre-fetched papers directly
        pass
    elif dois is None and query is None:
        raise ValueError("Must provide 'query', 'dois', or 'papers'")
    elif dois is None:
        # Get DOIs from search
        results = search(query, limit=limit, offset=offset)
        dois = [w.doi for w in results.works]
        # Fetch full metadata
        works = get_many(dois)
        papers = [w.to_dict() for w in works]
    else:
        # Fetch full metadata for DOIs
        works = get_many(dois)
        papers = [w.to_dict() for w in works]

    # Save cache
    cache_file = _cache_path(name)
    with open(cache_file, "w") as f:
        json.dump(papers, f)

    # Save metadata
    meta = {
        "name": name,
        "query": query,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "paper_count": len(papers),
        "dois_requested": len(dois) if dois else len(papers),
    }
    with open(_meta_path(name), "w") as f:
        json.dump(meta, f, indent=2)

    return CacheInfo(
        name=name,
        path=str(cache_file),
        size_bytes=cache_file.stat().st_size,
        paper_count=len(papers),
        created_at=meta["created_at"],
        query=query,
    )


def append(
    name: str,
    query: Optional[str] = None,
    dois: Optional[List[str]] = None,
    limit: int = 1000,
    offset: int = 0,
) -> CacheInfo:
    """Append papers to existing cache.

    Args:
        name: Existing cache name
        query: FTS search query (if dois not provided)
        dois: Explicit list of DOIs to add
        limit: Max papers to fetch (for query mode)
        offset: Offset for pagination (for query mode)

    Returns:
        Updated CacheInfo
    """
    if not exists(name):
        return create(name, query=query, dois=dois, limit=limit, offset=offset)

    # Load existing
    existing = load(name)
    existing_dois = {p["doi"] for p in existing}

    # Get new DOIs
    if dois is None and query is not None:
        results = search(query, limit=limit, offset=offset)
        dois = [w.doi for w in results.works]
    elif dois is None:
        raise ValueError("Must provide either 'query' or 'dois'")

    # Filter out already cached
    new_dois = [d for d in dois if d not in existing_dois]

    if new_dois:
        # Fetch new metadata
        new_works = get_many(new_dois)
        new_papers = [w.to_dict() for w in new_works]

        # Combine and save
        all_papers = existing + new_papers
        cache_file = _cache_path(name)
        with open(cache_file, "w") as f:
            json.dump(all_papers, f)

        # Update metadata
        meta_file = _meta_path(name)
        if meta_file.exists():
            with open(meta_file) as f:
                meta = json.load(f)
        else:
            meta = {"name": name}

        meta["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        meta["paper_count"] = len(all_papers)

        with open(meta_file, "w") as f:
            json.dump(meta, f, indent=2)

        return info(name)

    return info(name)


def load(name: str) -> List[Dict[str, Any]]:
    """Load raw cache data.

    Args:
        name: Cache name

    Returns:
        List of paper dictionaries with full metadata
    """
    cache_file = _cache_path(name)
    if not cache_file.exists():
        raise FileNotFoundError(f"Cache not found: {name}")

    with open(cache_file) as f:
        return json.load(f)


def query(
    name: str,
    fields: Optional[List[str]] = None,
    include_abstract: bool = False,
    include_references: bool = False,
    include_citations: bool = False,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
    journal: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Query cache with field filtering.

    Args:
        name: Cache name
        fields: Explicit field list (overrides include_* flags)
        include_abstract: Include abstract field
        include_references: Include references list
        include_citations: Include citation_count
        year_min: Filter by minimum year
        year_max: Filter by maximum year
        journal: Filter by journal name (substring match)
        limit: Max results to return

    Returns:
        Filtered list of paper dictionaries

    Example:
        >>> # Minimal query
        >>> papers = query("epilepsy", fields=["doi", "title", "year"])
        >>> # With filters
        >>> papers = query("epilepsy", year_min=2020, include_citations=True)
    """
    papers = load(name)

    # Apply filters
    if year_min is not None:
        papers = [p for p in papers if p.get("year") and p["year"] >= year_min]
    if year_max is not None:
        papers = [p for p in papers if p.get("year") and p["year"] <= year_max]
    if journal is not None:
        journal_lower = journal.lower()
        papers = [
            p
            for p in papers
            if p.get("journal") and journal_lower in p["journal"].lower()
        ]

    # Apply limit
    if limit is not None:
        papers = papers[:limit]

    # Field projection
    if fields is not None:
        # Explicit field list
        papers = [{k: p.get(k) for k in fields if k in p} for p in papers]
    else:
        # Build field list from flags
        base_fields = {"doi", "title", "authors", "year", "journal"}
        if include_abstract:
            base_fields.add("abstract")
        if include_references:
            base_fields.add("references")
        if include_citations:
            base_fields.add("citation_count")

        papers = [{k: p.get(k) for k in base_fields if k in p} for p in papers]

    return papers


def query_dois(name: str) -> List[str]:
    """Get just DOIs from cache.

    Args:
        name: Cache name

    Returns:
        List of DOIs
    """
    papers = load(name)
    return [p["doi"] for p in papers if p.get("doi")]


def stats(name: str) -> Dict[str, Any]:
    """Get cache statistics.

    Args:
        name: Cache name

    Returns:
        Dictionary with statistics
    """
    papers = load(name)

    # Year distribution
    years = [p.get("year") for p in papers if p.get("year")]
    year_dist = {}
    for y in years:
        year_dist[y] = year_dist.get(y, 0) + 1

    # Journal distribution
    journals = [p.get("journal") for p in papers if p.get("journal")]
    journal_dist = {}
    for j in journals:
        journal_dist[j] = journal_dist.get(j, 0) + 1
    top_journals = sorted(journal_dist.items(), key=lambda x: -x[1])[:20]

    # Abstract coverage
    with_abstract = sum(1 for p in papers if p.get("abstract"))

    # Citation stats
    citations = [p.get("citation_count", 0) for p in papers if p.get("citation_count")]

    return {
        "paper_count": len(papers),
        "year_range": {
            "min": min(years) if years else None,
            "max": max(years) if years else None,
        },
        "year_distribution": dict(sorted(year_dist.items())),
        "with_abstract": with_abstract,
        "abstract_coverage": round(with_abstract / len(papers) * 100, 1)
        if papers
        else 0,
        "top_journals": [{"journal": j, "count": c} for j, c in top_journals],
        "citation_stats": {
            "total": sum(citations),
            "mean": round(sum(citations) / len(citations), 1) if citations else 0,
            "max": max(citations) if citations else 0,
        }
        if citations
        else None,
    }


def info(name: str) -> CacheInfo:
    """Get cache information.

    Args:
        name: Cache name

    Returns:
        CacheInfo object
    """
    cache_file = _cache_path(name)
    if not cache_file.exists():
        raise FileNotFoundError(f"Cache not found: {name}")

    meta_file = _meta_path(name)
    meta = {}
    if meta_file.exists():
        with open(meta_file) as f:
            meta = json.load(f)

    papers = load(name)

    return CacheInfo(
        name=name,
        path=str(cache_file),
        size_bytes=cache_file.stat().st_size,
        paper_count=len(papers),
        created_at=meta.get("created_at", "unknown"),
        query=meta.get("query"),
    )


def exists(name: str) -> bool:
    """Check if cache exists.

    Args:
        name: Cache name

    Returns:
        True if cache exists
    """
    return _cache_path(name).exists()


def list_caches() -> List[CacheInfo]:
    """List all available caches.

    Returns:
        List of CacheInfo objects
    """
    cache_dir = _get_cache_dir()
    caches = []

    for f in cache_dir.glob("*.json"):
        if f.name.endswith(".meta.json"):
            continue
        name = f.stem
        try:
            caches.append(info(name))
        except Exception:
            pass

    return sorted(caches, key=lambda c: c.name)


def delete(name: str) -> bool:
    """Delete a cache.

    Args:
        name: Cache name

    Returns:
        True if deleted
    """
    cache_file = _cache_path(name)
    meta_file = _meta_path(name)

    deleted = False
    if cache_file.exists():
        cache_file.unlink()
        deleted = True
    if meta_file.exists():
        meta_file.unlink()

    return deleted



# Re-export from cache_export for backwards compatibility
from .cache_export import export

__all__ = [
    "CacheInfo",
    "create",
    "append",
    "load",
    "query",
    "query_dois",
    "stats",
    "info",
    "exists",
    "list_caches",
    "delete",
    "export",
]
