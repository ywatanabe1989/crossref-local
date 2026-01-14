"""Main API for crossref_local.

Supports two modes:
- local: Direct database access (requires database file)
- remote: HTTP API access (requires API server)

Mode is auto-detected or can be set explicitly via:
- CROSSREF_LOCAL_MODE environment variable ("local" or "remote")
- CROSSREF_LOCAL_API environment variable (API URL)
- configure() or configure_remote() functions
"""

from typing import List, Optional

from .config import Config
from .db import get_db, close_db
from .models import Work, SearchResult
from . import fts


def _get_remote_client():
    """Get remote client (lazy import to avoid circular dependency)."""
    from .remote import RemoteClient

    return RemoteClient(Config.get_api_url())


def search(
    query: str,
    limit: int = 10,
    offset: int = 0,
) -> SearchResult:
    """
    Full-text search across works.

    Uses FTS5 index for fast searching across titles, abstracts, and authors.

    Args:
        query: Search query (supports FTS5 syntax)
        limit: Maximum results to return
        offset: Skip first N results (for pagination)

    Returns:
        SearchResult with matching works

    Example:
        >>> from crossref_local import search
        >>> results = search("machine learning")
        >>> print(f"Found {results.total} matches")
    """
    if Config.get_mode() == "remote":
        client = _get_remote_client()
        return client.search(query=query, limit=limit)
    return fts.search(query, limit, offset)


def count(query: str) -> int:
    """
    Count matching works without fetching results.

    Args:
        query: FTS5 search query

    Returns:
        Number of matching works
    """
    if Config.get_mode() == "remote":
        client = _get_remote_client()
        result = client.search(query=query, limit=1)
        return result.total
    return fts.count(query)


def get(doi: str) -> Optional[Work]:
    """
    Get a work by DOI.

    Args:
        doi: Digital Object Identifier

    Returns:
        Work object or None if not found

    Example:
        >>> from crossref_local import get
        >>> work = get("10.1038/nature12373")
        >>> print(work.title)
    """
    if Config.get_mode() == "remote":
        client = _get_remote_client()
        return client.get(doi)
    db = get_db()
    metadata = db.get_metadata(doi)
    if metadata:
        return Work.from_metadata(doi, metadata)
    return None


def get_many(dois: List[str]) -> List[Work]:
    """
    Get multiple works by DOI.

    Args:
        dois: List of DOIs

    Returns:
        List of Work objects (missing DOIs are skipped)
    """
    if Config.get_mode() == "remote":
        client = _get_remote_client()
        return client.get_many(dois)
    db = get_db()
    works = []
    for doi in dois:
        metadata = db.get_metadata(doi)
        if metadata:
            works.append(Work.from_metadata(doi, metadata))
    return works


def exists(doi: str) -> bool:
    """
    Check if a DOI exists in the database.

    Args:
        doi: Digital Object Identifier

    Returns:
        True if DOI exists
    """
    if Config.get_mode() == "remote":
        client = _get_remote_client()
        return client.exists(doi)
    db = get_db()
    row = db.fetchone("SELECT 1 FROM works WHERE doi = ?", (doi,))
    return row is not None


def configure(db_path: str) -> None:
    """
    Configure for local database access.

    Args:
        db_path: Path to CrossRef SQLite database

    Example:
        >>> from crossref_local import configure
        >>> configure("/path/to/crossref.db")
    """
    Config.set_db_path(db_path)
    close_db()  # Reset singleton to use new path


def configure_remote(api_url: str = "http://localhost:3333") -> None:
    """
    Configure for remote API access.

    Args:
        api_url: URL of CrossRef Local API server

    Example:
        >>> from crossref_local import configure_remote
        >>> configure_remote("http://localhost:3333")
        >>> # Or via SSH tunnel:
        >>> # ssh -L 3333:127.0.0.1:3333 nas
        >>> configure_remote()  # Uses default localhost:3333
    """
    Config.set_api_url(api_url)


def get_mode() -> str:
    """
    Get current mode.

    Returns:
        "local" or "remote"
    """
    return Config.get_mode()


def info() -> dict:
    """
    Get database/API information.

    Returns:
        Dictionary with database stats and mode info
    """
    mode = Config.get_mode()

    if mode == "remote":
        client = _get_remote_client()
        remote_info = client.info()
        return {"mode": "remote", **remote_info}

    db = get_db()

    # Get work count
    row = db.fetchone("SELECT COUNT(*) as count FROM works")
    work_count = row["count"] if row else 0

    # Get FTS count
    try:
        row = db.fetchone("SELECT COUNT(*) as count FROM works_fts")
        fts_count = row["count"] if row else 0
    except Exception:
        fts_count = 0

    # Get citations count
    try:
        row = db.fetchone("SELECT COUNT(*) as count FROM citations")
        citation_count = row["count"] if row else 0
    except Exception:
        citation_count = 0

    return {
        "mode": "local",
        "db_path": str(Config.get_db_path()),
        "works": work_count,
        "fts_indexed": fts_count,
        "citations": citation_count,
    }
