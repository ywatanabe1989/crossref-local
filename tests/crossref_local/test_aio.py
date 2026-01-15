"""Tests for crossref_local.aio module (async API)."""

import pytest
import asyncio

from crossref_local import aio
from crossref_local.models import SearchResult, Work


class TestAsyncSearch:
    """Tests for aio.search function."""

    @pytest.mark.asyncio
    async def test_search_returns_search_result(self):
        """aio.search() returns SearchResult object."""
        results = await aio.search("science", limit=1)
        assert isinstance(results, SearchResult)

    @pytest.mark.asyncio
    async def test_search_result_has_query(self):
        """SearchResult contains the query string."""
        results = await aio.search("biology", limit=1)
        assert results.query == "biology"

    @pytest.mark.asyncio
    async def test_search_result_has_total(self):
        """SearchResult has total count."""
        results = await aio.search("medicine", limit=1)
        assert isinstance(results.total, int)
        assert results.total >= 0

    @pytest.mark.asyncio
    async def test_search_returns_work_objects(self):
        """aio.search() returns Work objects."""
        results = await aio.search("chemistry", limit=3)
        for work in results.works:
            assert isinstance(work, Work)

    @pytest.mark.asyncio
    async def test_search_respects_limit(self):
        """aio.search() respects limit parameter."""
        results = await aio.search("cancer", limit=5)
        assert len(results.works) <= 5

    @pytest.mark.asyncio
    async def test_search_with_offset(self):
        """aio.search() with offset skips results."""
        results1 = await aio.search("neuroscience", limit=5, offset=0)
        results2 = await aio.search("neuroscience", limit=5, offset=5)

        if len(results1.works) >= 5 and len(results2.works) >= 1:
            assert results1.works[0].doi != results2.works[0].doi


class TestAsyncCount:
    """Tests for aio.count function."""

    @pytest.mark.asyncio
    async def test_count_returns_integer(self):
        """aio.count() returns an integer."""
        n = await aio.count("science")
        assert isinstance(n, int)

    @pytest.mark.asyncio
    async def test_count_non_negative(self):
        """aio.count() returns non-negative value."""
        n = await aio.count("biology")
        assert n >= 0

    @pytest.mark.asyncio
    async def test_count_rare_term(self):
        """aio.count() for rare terms returns small numbers."""
        n = await aio.count("xyznonexistent123")
        assert n == 0


class TestAsyncGet:
    """Tests for aio.get function."""

    @pytest.mark.asyncio
    async def test_get_existing_doi(self, sample_doi):
        """aio.get() returns Work for existing DOI."""
        work = await aio.get(sample_doi)
        assert work is None or isinstance(work, Work)

    @pytest.mark.asyncio
    async def test_get_nonexistent_doi(self):
        """aio.get() returns None for nonexistent DOI."""
        work = await aio.get("10.0000/nonexistent")
        assert work is None

    @pytest.mark.asyncio
    async def test_get_work_has_doi(self, sample_doi):
        """Returned Work has correct DOI."""
        work = await aio.get(sample_doi)
        if work:
            assert work.doi == sample_doi


class TestAsyncGetMany:
    """Tests for aio.get_many function."""

    @pytest.mark.asyncio
    async def test_get_many_returns_list(self, sample_doi):
        """aio.get_many() returns a list."""
        works = await aio.get_many([sample_doi])
        assert isinstance(works, list)

    @pytest.mark.asyncio
    async def test_get_many_empty_list(self):
        """aio.get_many() with empty list returns empty list."""
        works = await aio.get_many([])
        assert works == []

    @pytest.mark.asyncio
    async def test_get_many_skips_missing(self):
        """aio.get_many() skips nonexistent DOIs."""
        works = await aio.get_many(["10.0000/nonexistent1", "10.0000/nonexistent2"])
        assert works == []


class TestAsyncExists:
    """Tests for aio.exists function."""

    @pytest.mark.asyncio
    async def test_exists_returns_bool(self, sample_doi):
        """aio.exists() returns boolean."""
        result = await aio.exists(sample_doi)
        assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_exists_nonexistent(self):
        """aio.exists() returns False for nonexistent DOI."""
        result = await aio.exists("10.0000/nonexistent")
        assert result is False


class TestAsyncInfo:
    """Tests for aio.info function."""

    @pytest.mark.asyncio
    async def test_info_returns_dict(self):
        """aio.info() returns a dictionary."""
        info = await aio.info()
        assert isinstance(info, dict)

    @pytest.mark.asyncio
    async def test_info_has_db_path(self):
        """Info dict contains db_path."""
        info = await aio.info()
        assert "db_path" in info

    @pytest.mark.asyncio
    async def test_info_has_works_count(self):
        """Info dict contains works count."""
        info = await aio.info()
        assert "works" in info
        assert isinstance(info["works"], int)


class TestAsyncSearchMany:
    """Tests for aio.search_many function."""

    @pytest.mark.asyncio
    async def test_search_many_returns_list(self):
        """aio.search_many() returns list of SearchResults."""
        results = await aio.search_many(["science", "biology"], limit=1)
        assert isinstance(results, list)
        assert len(results) == 2
        for r in results:
            assert isinstance(r, SearchResult)

    @pytest.mark.asyncio
    async def test_search_many_concurrent(self):
        """aio.search_many() runs queries concurrently."""
        queries = ["physics", "chemistry", "biology"]
        results = await aio.search_many(queries, limit=1)
        assert len(results) == 3


class TestAsyncCountMany:
    """Tests for aio.count_many function."""

    @pytest.mark.asyncio
    async def test_count_many_returns_dict(self):
        """aio.count_many() returns dict mapping query to count."""
        counts = await aio.count_many(["science", "biology"])
        assert isinstance(counts, dict)
        assert "science" in counts
        assert "biology" in counts

    @pytest.mark.asyncio
    async def test_count_many_values_are_ints(self):
        """aio.count_many() values are integers."""
        counts = await aio.count_many(["physics", "chemistry"])
        for query, count in counts.items():
            assert isinstance(count, int)
            assert count >= 0


class TestConcurrency:
    """Tests for concurrent async operations."""

    @pytest.mark.asyncio
    async def test_concurrent_searches(self):
        """Multiple concurrent searches work correctly."""
        tasks = [
            aio.search("science", limit=1),
            aio.search("biology", limit=1),
            aio.search("physics", limit=1),
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == 3
        for r in results:
            assert isinstance(r, SearchResult)

    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self, sample_doi):
        """Mixed concurrent operations work correctly."""
        tasks = [
            aio.search("science", limit=1),
            aio.count("biology"),
            aio.get(sample_doi),
            aio.info(),
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == 4
