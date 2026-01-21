"""Tests for crossref_local.api module."""

import pytest
from crossref_local import search, get, count, info, exists
from crossref_local.models import Work, SearchResult


class TestSearch:
    """Tests for search function."""

    def test_search_returns_search_result(self):
        """search() returns a SearchResult object."""
        results = search("neuroscience", limit=1)
        assert isinstance(results, SearchResult)

    def test_search_result_has_expected_attributes(self):
        """SearchResult has query, total, elapsed_ms, works."""
        results = search("neuroscience", limit=1)
        assert hasattr(results, "query")
        assert hasattr(results, "total")
        assert hasattr(results, "elapsed_ms")
        assert hasattr(results, "works")

    def test_search_returns_works(self):
        """search() returns Work objects."""
        results = search("cancer", limit=3)
        assert len(results.works) <= 3
        for work in results.works:
            assert isinstance(work, Work)

    def test_search_limit_respected(self):
        """Limit parameter controls number of results."""
        results = search("neuroscience", limit=5)
        assert len(results.works) <= 5

    def test_search_offset_works(self):
        """Offset parameter skips results."""
        results1 = search("neuroscience", limit=5, offset=0)
        results2 = search("neuroscience", limit=5, offset=5)
        if len(results1.works) >= 5 and len(results2.works) >= 1:
            # First result of second query should differ from first query
            assert results1.works[0].doi != results2.works[0].doi


class TestGet:
    """Tests for get function."""

    def test_get_existing_doi(self):
        """get() returns Work for existing DOI."""
        # First find a valid DOI from search
        results = search("neuroscience", limit=1)
        if results.works:
            doi = results.works[0].doi
            work = get(doi)
            assert work is not None
            assert isinstance(work, Work)
            assert work.doi == doi

    def test_get_nonexistent_doi(self):
        """get() returns None for nonexistent DOI."""
        work = get("10.9999/nonexistent.doi.12345")
        assert work is None

    def test_get_work_has_metadata(self):
        """Work from get() has expected metadata."""
        results = search("cancer", limit=1)
        if results.works:
            work = get(results.works[0].doi)
            assert work is not None
            assert work.doi is not None


class TestCount:
    """Tests for count function."""

    def test_count_returns_integer(self):
        """count() returns an integer."""
        n = count("neuroscience")
        assert isinstance(n, int)
        assert n > 0

    def test_count_search_term(self):
        """count() returns positive number for valid search."""
        n = count("cancer")
        assert n > 0


class TestExists:
    """Tests for exists function."""

    def test_exists_true_for_valid_doi(self):
        """exists() returns True for valid DOI."""
        results = search("quantum", limit=1)
        if results.works:
            assert exists(results.works[0].doi) is True

    def test_exists_false_for_invalid_doi(self):
        """exists() returns False for invalid DOI."""
        assert exists("10.9999/nonexistent") is False


class TestInfo:
    """Tests for info function."""

    def test_info_returns_dict(self):
        """info() returns a dictionary."""
        db_info = info()
        assert isinstance(db_info, dict)

    def test_info_has_expected_keys(self):
        """info() dict has expected keys."""
        db_info = info()
        assert "db_path" in db_info
        assert "works" in db_info
        assert "fts_indexed" in db_info
        assert "citations" in db_info

    def test_info_works_count(self):
        """info() reports positive works count."""
        db_info = info()
        assert db_info["works"] > 0


class TestEnrich:
    """Tests for enrich function."""

    def test_enrich_returns_search_result(self):
        """enrich() returns a SearchResult object."""
        from crossref_local import enrich

        results = search("neuroscience", limit=2)
        enriched = enrich(results)
        assert isinstance(enriched, SearchResult)

    def test_enrich_preserves_total(self):
        """enrich() preserves total count."""
        from crossref_local import enrich

        results = search("cancer", limit=3)
        enriched = enrich(results)
        assert enriched.total == results.total

    def test_enrich_works_have_metadata(self):
        """Enriched works have full metadata."""
        from crossref_local import enrich

        results = search("quantum", limit=1)
        if results.works:
            enriched = enrich(results)
            assert len(enriched.works) == len(results.works)


class TestEnrichDois:
    """Tests for enrich_dois function."""

    def test_enrich_dois_returns_list(self):
        """enrich_dois() returns a list of Work objects."""
        from crossref_local import enrich_dois

        results = search("machine learning", limit=2)
        dois = [w.doi for w in results.works]
        if dois:
            works = enrich_dois(dois)
            assert isinstance(works, list)
            for work in works:
                assert isinstance(work, Work)

    def test_enrich_dois_returns_correct_count(self):
        """enrich_dois() returns works for valid DOIs."""
        from crossref_local import enrich_dois

        results = search("neuroscience", limit=3)
        dois = [w.doi for w in results.works]
        if dois:
            works = enrich_dois(dois)
            assert len(works) <= len(dois)

    def test_enrich_dois_empty_list(self):
        """enrich_dois() handles empty list."""
        from crossref_local import enrich_dois

        works = enrich_dois([])
        assert works == []


if __name__ == "__main__":
    import os
    import pytest

    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/crossref_local/src/crossref_local/api.py
# --------------------------------------------------------------------------------
# """Main API for crossref_local."""
#
# from typing import List, Optional
#
# from .config import Config
# from .db import Database, get_db, close_db, connection
# from .models import Work, SearchResult
# from . import fts
#
#
# def search(
#     query: str,
#     limit: int = 10,
#     offset: int = 0,
# ) -> SearchResult:
#     """
#     Full-text search across works.
#
#     Uses FTS5 index for fast searching across titles, abstracts, and authors.
#
#     Args:
#         query: Search query (supports FTS5 syntax)
#         limit: Maximum results to return
#         offset: Skip first N results (for pagination)
#
#     Returns:
#         SearchResult with matching works
#
#     Example:
#         >>> from crossref_local import search
#         >>> results = search("machine learning")
#         >>> print(f"Found {results.total} matches")
#     """
#     return fts.search(query, limit, offset)
#
#
# def count(query: str) -> int:
#     """
#     Count matching works without fetching results.
#
#     Args:
#         query: FTS5 search query
#
#     Returns:
#         Number of matching works
#     """
#     return fts.count(query)
#
#
# def get(doi: str) -> Optional[Work]:
#     """
#     Get a work by DOI.
#
#     Args:
#         doi: Digital Object Identifier
#
#     Returns:
#         Work object or None if not found
#
#     Example:
#         >>> from crossref_local import get
#         >>> work = get("10.1038/nature12373")
#         >>> print(work.title)
#     """
#     db = get_db()
#     metadata = db.get_metadata(doi)
#     if metadata:
#         return Work.from_metadata(doi, metadata)
#     return None
#
#
# def get_many(dois: List[str]) -> List[Work]:
#     """
#     Get multiple works by DOI.
#
#     Args:
#         dois: List of DOIs
#
#     Returns:
#         List of Work objects (missing DOIs are skipped)
#     """
#     db = get_db()
#     works = []
#     for doi in dois:
#         metadata = db.get_metadata(doi)
#         if metadata:
#             works.append(Work.from_metadata(doi, metadata))
#     return works
#
#
# def exists(doi: str) -> bool:
#     """
#     Check if a DOI exists in the database.
#
#     Args:
#         doi: Digital Object Identifier
#
#     Returns:
#         True if DOI exists
#     """
#     db = get_db()
#     row = db.fetchone("SELECT 1 FROM works WHERE doi = ?", (doi,))
#     return row is not None
#
#
# def configure(db_path: str) -> None:
#     """
#     Configure database path.
#
#     Args:
#         db_path: Path to CrossRef SQLite database
#
#     Example:
#         >>> from crossref_local import configure
#         >>> configure("/path/to/crossref.db")
#     """
#     Config.set_db_path(db_path)
#     close_db()  # Reset singleton to use new path
#
#
# def info() -> dict:
#     """
#     Get database information.
#
#     Returns:
#         Dictionary with database stats
#     """
#     db = get_db()
#
#     # Get work count
#     row = db.fetchone("SELECT COUNT(*) as count FROM works")
#     work_count = row["count"] if row else 0
#
#     # Get FTS count
#     try:
#         row = db.fetchone("SELECT COUNT(*) as count FROM works_fts")
#         fts_count = row["count"] if row else 0
#     except Exception:
#         fts_count = 0
#
#     # Get citations count
#     try:
#         row = db.fetchone("SELECT COUNT(*) as count FROM citations")
#         citation_count = row["count"] if row else 0
#     except Exception:
#         citation_count = 0
#
#     return {
#         "db_path": str(Config.get_db_path()),
#         "works": work_count,
#         "fts_indexed": fts_count,
#         "citations": citation_count,
#     }

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/crossref_local/src/crossref_local/api.py
# --------------------------------------------------------------------------------
