"""Tests for crossref_local.cache module."""

import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from crossref_local import cache
from crossref_local.cache import CacheInfo


class TestCacheBasics:
    """Tests for basic cache operations."""

    def test_cache_dir_creation(self):
        """Cache directory is created if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CROSSREF_LOCAL_CACHE_DIR": tmpdir}):
                cache_dir = cache._get_cache_dir()
                assert cache_dir.exists()

    def test_cache_path(self):
        """Cache path is correctly formed."""
        path = cache._cache_path("test")
        assert path.name == "test.json"

    def test_meta_path(self):
        """Metadata path is correctly formed."""
        path = cache._meta_path("test")
        assert path.name == "test.meta.json"


class TestCacheInfo:
    """Tests for CacheInfo dataclass."""

    def test_cache_info_to_dict(self):
        """CacheInfo.to_dict() returns expected keys."""
        info = CacheInfo(
            name="test",
            path="/tmp/test.json",
            size_bytes=1024,
            paper_count=10,
            created_at="2024-01-01 12:00:00",
            query="test query",
        )
        d = info.to_dict()
        assert d["name"] == "test"
        assert d["paper_count"] == 10
        assert d["size_mb"] == 0.0  # 1024 bytes = 0.001 MB rounded
        assert d["query"] == "test query"


class TestCacheOperations:
    """Tests for cache CRUD operations."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CROSSREF_LOCAL_CACHE_DIR": tmpdir}):
                yield tmpdir

    def test_create_with_dois(self, temp_cache_dir):
        """Cache can be created from DOI list."""
        # Mock get_many to return fake papers
        fake_works = [
            MagicMock(
                to_dict=lambda: {
                    "doi": "10.1234/test1",
                    "title": "Test Paper 1",
                    "year": 2020,
                }
            ),
            MagicMock(
                to_dict=lambda: {
                    "doi": "10.1234/test2",
                    "title": "Test Paper 2",
                    "year": 2021,
                }
            ),
        ]

        with patch("crossref_local.cache.get_many", return_value=fake_works):
            info = cache.create("test", dois=["10.1234/test1", "10.1234/test2"])

        assert info.name == "test"
        assert info.paper_count == 2
        assert cache.exists("test")

    def test_load_cache(self, temp_cache_dir):
        """Cache can be loaded after creation."""
        fake_works = [
            MagicMock(to_dict=lambda: {"doi": "10.1234/test", "title": "Test"})
        ]

        with patch("crossref_local.cache.get_many", return_value=fake_works):
            cache.create("loadtest", dois=["10.1234/test"])

        papers = cache.load("loadtest")
        assert len(papers) == 1
        assert papers[0]["doi"] == "10.1234/test"

    def test_query_fields(self, temp_cache_dir):
        """Query returns only requested fields."""
        fake_works = [
            MagicMock(
                to_dict=lambda: {
                    "doi": "10.1234/test",
                    "title": "Test Paper",
                    "abstract": "Long abstract...",
                    "year": 2020,
                    "citation_count": 50,
                }
            )
        ]

        with patch("crossref_local.cache.get_many", return_value=fake_works):
            cache.create("fieldtest", dois=["10.1234/test"])

        # Query with explicit fields
        papers = cache.query("fieldtest", fields=["doi", "year"])
        assert len(papers) == 1
        assert "doi" in papers[0]
        assert "year" in papers[0]
        assert "abstract" not in papers[0]
        assert "title" not in papers[0]

    def test_query_filters(self, temp_cache_dir):
        """Query filters work correctly."""
        fake_works = [
            MagicMock(to_dict=lambda i=i: {"doi": f"10.1234/test{i}", "year": 2018 + i})
            for i in range(5)
        ]

        with patch("crossref_local.cache.get_many", return_value=fake_works):
            cache.create("filtertest", dois=[f"10.1234/test{i}" for i in range(5)])

        # Filter by year
        papers = cache.query("filtertest", year_min=2020)
        assert all(p["year"] >= 2020 for p in papers)

    def test_stats(self, temp_cache_dir):
        """Stats returns expected statistics."""
        fake_works = [
            MagicMock(
                to_dict=lambda: {
                    "doi": "10.1234/test",
                    "year": 2020,
                    "journal": "Test Journal",
                    "abstract": "Abstract text",
                    "citation_count": 10,
                }
            )
        ]

        with patch("crossref_local.cache.get_many", return_value=fake_works):
            cache.create("statstest", dois=["10.1234/test"])

        stats = cache.stats("statstest")
        assert stats["paper_count"] == 1
        assert stats["year_range"]["min"] == 2020
        assert stats["with_abstract"] == 1

    def test_delete(self, temp_cache_dir):
        """Cache can be deleted."""
        fake_works = [MagicMock(to_dict=lambda: {"doi": "10.1234/test"})]

        with patch("crossref_local.cache.get_many", return_value=fake_works):
            cache.create("deltest", dois=["10.1234/test"])

        assert cache.exists("deltest")
        cache.delete("deltest")
        assert not cache.exists("deltest")

    def test_list_caches(self, temp_cache_dir):
        """List caches returns all caches."""
        fake_works = [MagicMock(to_dict=lambda: {"doi": "10.1234/test"})]

        with patch("crossref_local.cache.get_many", return_value=fake_works):
            cache.create("list1", dois=["10.1234/test"])
            cache.create("list2", dois=["10.1234/test"])

        caches = cache.list_caches()
        names = [c.name for c in caches]
        assert "list1" in names
        assert "list2" in names


class TestCacheExport:
    """Tests for cache export functionality."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"CROSSREF_LOCAL_CACHE_DIR": tmpdir}):
                yield tmpdir

    def test_export_json(self, temp_cache_dir):
        """Export to JSON works."""
        fake_works = [
            MagicMock(
                to_dict=lambda: {"doi": "10.1234/test", "title": "Test", "year": 2020}
            )
        ]

        with patch("crossref_local.cache.get_many", return_value=fake_works):
            cache.create("exportjson", dois=["10.1234/test"])

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            output = f.name

        try:
            cache.export("exportjson", output, format="json")
            with open(output) as f:
                data = json.load(f)
            assert len(data) == 1
            assert data[0]["doi"] == "10.1234/test"
        finally:
            os.unlink(output)

    def test_export_dois(self, temp_cache_dir):
        """Export DOIs only works."""
        fake_works = [
            MagicMock(to_dict=lambda: {"doi": "10.1234/test1"}),
            MagicMock(to_dict=lambda: {"doi": "10.1234/test2"}),
        ]

        with patch("crossref_local.cache.get_many", return_value=fake_works):
            cache.create("exportdois", dois=["10.1234/test1", "10.1234/test2"])

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            output = f.name

        try:
            cache.export("exportdois", output, format="dois")
            with open(output) as f:
                lines = f.read().strip().split("\n")
            assert len(lines) == 2
            assert "10.1234/test1" in lines
        finally:
            os.unlink(output)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
