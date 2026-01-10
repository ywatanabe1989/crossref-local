"""Main API for crossref_local."""

from typing import List, Optional

from .config import Config
from .db import Database, get_db, close_db, connection
from .models import Work, SearchResult
from . import fts


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
    return fts.search(query, limit, offset)


def count(query: str) -> int:
    """
    Count matching works without fetching results.

    Args:
        query: FTS5 search query

    Returns:
        Number of matching works
    """
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
    db = get_db()
    row = db.fetchone("SELECT 1 FROM works WHERE doi = ?", (doi,))
    return row is not None


def configure(db_path: str) -> None:
    """
    Configure database path.

    Args:
        db_path: Path to CrossRef SQLite database

    Example:
        >>> from crossref_local import configure
        >>> configure("/path/to/crossref.db")
    """
    Config.set_db_path(db_path)
    close_db()  # Reset singleton to use new path


def info() -> dict:
    """
    Get database information.

    Returns:
        Dictionary with database stats
    """
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
        "db_path": str(Config.get_db_path()),
        "works": work_count,
        "fts_indexed": fts_count,
        "citations": citation_count,
    }
