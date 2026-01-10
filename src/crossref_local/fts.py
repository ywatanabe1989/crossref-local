"""Full-text search using FTS5."""

import time
from typing import List, Optional

from .db import Database, get_db
from .models import Work, SearchResult


def search(
    query: str,
    limit: int = 10,
    offset: int = 0,
    db: Optional[Database] = None,
) -> SearchResult:
    """
    Full-text search across works.

    Uses FTS5 index for fast searching across titles, abstracts, and authors.

    Args:
        query: Search query (supports FTS5 syntax like AND, OR, NOT, "phrases")
        limit: Maximum results to return
        offset: Skip first N results (for pagination)
        db: Database connection (uses singleton if not provided)

    Returns:
        SearchResult with matching works

    Example:
        >>> results = search("hippocampal sharp wave ripples")
        >>> print(f"Found {results.total} matches in {results.elapsed_ms:.1f}ms")
        >>> for work in results:
        ...     print(f"{work.title} ({work.year})")
    """
    if db is None:
        db = get_db()

    start = time.perf_counter()

    # Get total count
    count_row = db.fetchone(
        "SELECT COUNT(*) as total FROM works_fts WHERE works_fts MATCH ?",
        (query,)
    )
    total = count_row["total"] if count_row else 0

    # Get matching works with metadata
    rows = db.fetchall(
        """
        SELECT w.doi, w.metadata
        FROM works_fts f
        JOIN works w ON f.rowid = w.rowid
        WHERE works_fts MATCH ?
        LIMIT ? OFFSET ?
        """,
        (query, limit, offset)
    )

    elapsed_ms = (time.perf_counter() - start) * 1000

    # Convert to Work objects
    works = []
    for row in rows:
        metadata = db._decompress_metadata(row["metadata"])
        works.append(Work.from_metadata(row["doi"], metadata))

    return SearchResult(
        works=works,
        total=total,
        query=query,
        elapsed_ms=elapsed_ms,
    )


def count(query: str, db: Optional[Database] = None) -> int:
    """
    Count matching works without fetching results.

    Args:
        query: FTS5 search query
        db: Database connection

    Returns:
        Number of matching works
    """
    if db is None:
        db = get_db()

    row = db.fetchone(
        "SELECT COUNT(*) as total FROM works_fts WHERE works_fts MATCH ?",
        (query,)
    )
    return row["total"] if row else 0


def search_dois(
    query: str,
    limit: int = 1000,
    db: Optional[Database] = None,
) -> List[str]:
    """
    Search and return only DOIs (faster than full search).

    Args:
        query: FTS5 search query
        limit: Maximum DOIs to return
        db: Database connection

    Returns:
        List of matching DOIs
    """
    if db is None:
        db = get_db()

    rows = db.fetchall(
        """
        SELECT w.doi
        FROM works_fts f
        JOIN works w ON f.rowid = w.rowid
        WHERE works_fts MATCH ?
        LIMIT ?
        """,
        (query, limit)
    )

    return [row["doi"] for row in rows]


# Thread-safe versions for async API
def _search_with_db(db: Database, query: str, limit: int, offset: int) -> SearchResult:
    """Search with explicit database connection (for thread-safe async)."""
    return search(query, limit, offset, db=db)


def _count_with_db(db: Database, query: str) -> int:
    """Count with explicit database connection (for thread-safe async)."""
    return count(query, db=db)
