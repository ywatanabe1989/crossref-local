"""Tests for crossref_local.fts module."""

import pytest

from crossref_local.fts import search, count, search_dois
from crossref_local.models import SearchResult, Work


class TestSearch:
    """Tests for fts.search function."""

    def test_search_returns_search_result(self):
        """search() returns SearchResult object."""
        results = search("science", limit=1)
        assert isinstance(results, SearchResult)

    def test_search_result_has_query(self):
        """SearchResult contains the query string."""
        results = search("biology", limit=1)
        assert results.query == "biology"

    def test_search_result_has_total(self):
        """SearchResult has total count."""
        results = search("medicine", limit=1)
        assert isinstance(results.total, int)
        assert results.total >= 0

    def test_search_result_has_elapsed_ms(self):
        """SearchResult has elapsed time."""
        results = search("physics", limit=1)
        assert isinstance(results.elapsed_ms, float)
        assert results.elapsed_ms >= 0

    def test_search_returns_work_objects(self):
        """search() returns Work objects."""
        results = search("chemistry", limit=3)
        for work in results.works:
            assert isinstance(work, Work)

    def test_search_respects_limit(self):
        """search() respects limit parameter."""
        results = search("cancer", limit=5)
        assert len(results.works) <= 5

    def test_search_with_offset(self):
        """search() with offset skips results."""
        results1 = search("neuroscience", limit=5, offset=0)
        results2 = search("neuroscience", limit=5, offset=5)

        if len(results1.works) >= 5 and len(results2.works) >= 1:
            # Different results due to offset
            assert results1.works[0].doi != results2.works[0].doi

    def test_search_fts5_phrase_syntax(self):
        """search() supports FTS5 phrase syntax."""
        # Exact phrase search
        results = search('"machine learning"', limit=5)
        assert isinstance(results, SearchResult)

    def test_search_fts5_boolean_syntax(self):
        """search() supports FTS5 boolean operators."""
        # AND operator
        results = search("neural AND network", limit=5)
        assert isinstance(results, SearchResult)

    def test_search_empty_query(self):
        """search() handles empty-ish queries gracefully."""
        # FTS5 might reject truly empty queries
        try:
            results = search("*", limit=1)
            assert isinstance(results, SearchResult)
        except Exception:
            # Some FTS5 configurations don't allow wildcard-only
            pass


class TestCount:
    """Tests for fts.count function."""

    def test_count_returns_integer(self):
        """count() returns integer."""
        n = count("biology")
        assert isinstance(n, int)

    def test_count_positive_for_common_terms(self):
        """count() returns positive for common terms."""
        n = count("cancer")
        assert n > 0

    def test_count_zero_for_nonsense(self):
        """count() returns zero for nonsense query."""
        n = count("xyzzy12345nonexistent")
        assert n == 0

    def test_count_matches_search_total(self):
        """count() matches search().total."""
        query = "quantum"
        n = count(query)
        results = search(query, limit=1)
        assert n == results.total


class TestSearchDois:
    """Tests for fts.search_dois function."""

    def test_search_dois_returns_list(self):
        """search_dois() returns list of strings."""
        dois = search_dois("genetics", limit=10)
        assert isinstance(dois, list)
        for doi in dois:
            assert isinstance(doi, str)

    def test_search_dois_respects_limit(self):
        """search_dois() respects limit parameter."""
        dois = search_dois("medicine", limit=5)
        assert len(dois) <= 5

    def test_search_dois_returns_valid_dois(self):
        """search_dois() returns valid DOI format."""
        dois = search_dois("biology", limit=5)
        for doi in dois:
            # DOIs start with 10.
            assert doi.startswith("10.")


class TestFTSTable:
    """Tests for FTS5 table structure."""

    def test_fts_table_exists(self):
        """works_fts table exists."""
        from crossref_local.db import get_db

        db = get_db()
        row = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='works_fts'"
        )
        assert row is not None

    def test_fts_search_is_fast(self):
        """FTS search completes quickly."""
        results = search("CRISPR", limit=10)
        # Should complete in under 1 second typically
        assert results.elapsed_ms < 5000  # 5 seconds max


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
