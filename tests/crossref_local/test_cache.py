"""Tests for crossref_local.cache module.

No mocks: cache.create() exposes a ``papers=`` injection seam that
bypasses the network. CROSSREF_LOCAL_CACHE_DIR is redirected via a
yield-based env fixture that points at tmp_path.
"""

import json
import os

import pytest

from crossref_local import cache
from crossref_local.cache import CacheInfo


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Redirect cache dir at tmp_path via env-var save/restore."""
    # Arrange
    saved = os.environ.get("CROSSREF_LOCAL_CACHE_DIR")
    os.environ["CROSSREF_LOCAL_CACHE_DIR"] = str(tmp_path)
    try:
        yield tmp_path
    finally:
        if saved is None:
            os.environ.pop("CROSSREF_LOCAL_CACHE_DIR", None)
        else:
            os.environ["CROSSREF_LOCAL_CACHE_DIR"] = saved


# ---------- cache directory + path helpers ----------


def test_get_cache_dir_creates_directory_when_missing(tmp_path):
    # Arrange
    target = tmp_path / "nested" / "cache"
    saved = os.environ.get("CROSSREF_LOCAL_CACHE_DIR")
    os.environ["CROSSREF_LOCAL_CACHE_DIR"] = str(target)
    # Act
    try:
        from crossref_local._cache.utils import get_cache_dir

        cache_dir = get_cache_dir()
    finally:
        if saved is None:
            os.environ.pop("CROSSREF_LOCAL_CACHE_DIR", None)
        else:
            os.environ["CROSSREF_LOCAL_CACHE_DIR"] = saved
    # Assert
    assert cache_dir.exists()


def test_cache_path_appends_dot_json_extension():
    # Arrange
    name = "test"
    # Act
    from crossref_local._cache.utils import cache_path

    path = cache_path(name)
    # Assert
    assert path.name == "test.json"


def test_meta_path_appends_dot_meta_json_extension():
    # Arrange
    name = "test"
    # Act
    from crossref_local._cache.utils import meta_path

    path = meta_path(name)
    # Assert
    assert path.name == "test.meta.json"


# ---------- CacheInfo.to_dict ----------


def test_cache_info_to_dict_preserves_name_field():
    # Arrange
    info = CacheInfo(
        name="test",
        path="/tmp/test.json",
        size_bytes=1024,
        paper_count=10,
        created_at="2024-01-01 12:00:00",
        query="test query",
    )
    # Act
    d = info.to_dict()
    # Assert
    assert d["name"] == "test"


def test_cache_info_to_dict_preserves_paper_count_field():
    # Arrange
    info = CacheInfo(
        name="test",
        path="/tmp/test.json",
        size_bytes=1024,
        paper_count=10,
        created_at="2024-01-01 12:00:00",
        query="test query",
    )
    # Act
    d = info.to_dict()
    # Assert
    assert d["paper_count"] == 10


def test_cache_info_to_dict_converts_bytes_to_megabytes_rounded():
    # Arrange
    info = CacheInfo(
        name="test",
        path="/tmp/test.json",
        size_bytes=1024,
        paper_count=10,
        created_at="2024-01-01 12:00:00",
        query="test query",
    )
    # Act
    d = info.to_dict()
    # Assert
    assert d["size_mb"] == 0.0  # 1024 bytes = 0.001 MB rounded


def test_cache_info_to_dict_preserves_query_field():
    # Arrange
    info = CacheInfo(
        name="test",
        path="/tmp/test.json",
        size_bytes=1024,
        paper_count=10,
        created_at="2024-01-01 12:00:00",
        query="test query",
    )
    # Act
    d = info.to_dict()
    # Assert
    assert d["query"] == "test query"


# ---------- cache.create with papers= injection seam ----------


def test_create_with_explicit_papers_returns_matching_name(temp_cache_dir):
    # Arrange
    papers = [
        {"doi": "10.1234/test1", "title": "Test Paper 1", "year": 2020},
        {"doi": "10.1234/test2", "title": "Test Paper 2", "year": 2021},
    ]
    # Act
    info = cache.create("test", papers=papers)
    # Assert
    assert info.name == "test"


def test_create_with_explicit_papers_sets_paper_count(temp_cache_dir):
    # Arrange
    papers = [
        {"doi": "10.1234/test1", "title": "Test Paper 1", "year": 2020},
        {"doi": "10.1234/test2", "title": "Test Paper 2", "year": 2021},
    ]
    # Act
    info = cache.create("test", papers=papers)
    # Assert
    assert info.paper_count == 2


def test_create_with_explicit_papers_makes_cache_discoverable(temp_cache_dir):
    # Arrange
    papers = [
        {"doi": "10.1234/test1", "title": "Test Paper 1", "year": 2020},
    ]
    # Act
    cache.create("test", papers=papers)
    # Assert
    assert cache.exists("test")


def test_load_round_trips_persisted_papers(temp_cache_dir):
    # Arrange
    papers = [{"doi": "10.1234/test", "title": "Test"}]
    cache.create("loadtest", papers=papers)
    # Act
    loaded = cache.load("loadtest")
    # Assert
    assert loaded == papers


# ---------- query field projection ----------


def test_query_with_explicit_fields_projects_only_requested_keys(temp_cache_dir):
    # Arrange
    papers = [
        {
            "doi": "10.1234/test",
            "title": "Test Paper",
            "abstract": "Long abstract...",
            "year": 2020,
            "citation_count": 50,
        }
    ]
    cache.create("fieldtest", papers=papers)
    # Act
    result = cache.query("fieldtest", fields=["doi", "year"])
    # Assert
    assert set(result[0].keys()) == {"doi", "year"}


def test_query_with_year_min_drops_older_papers(temp_cache_dir):
    # Arrange
    papers = [
        {"doi": f"10.1234/test{i}", "year": 2018 + i} for i in range(5)
    ]
    cache.create("filtertest", papers=papers)
    # Act
    result = cache.query("filtertest", year_min=2020)
    # Assert
    assert all(p["year"] >= 2020 for p in result)


# ---------- stats ----------


def test_stats_reports_paper_count(temp_cache_dir):
    # Arrange
    papers = [
        {
            "doi": "10.1234/test",
            "year": 2020,
            "journal": "Test Journal",
            "abstract": "Abstract text",
            "citation_count": 10,
        }
    ]
    cache.create("statstest", papers=papers)
    # Act
    stats = cache.stats("statstest")
    # Assert
    assert stats["paper_count"] == 1


def test_stats_reports_year_min_from_papers(temp_cache_dir):
    # Arrange
    papers = [
        {
            "doi": "10.1234/test",
            "year": 2020,
            "journal": "Test Journal",
            "abstract": "Abstract text",
            "citation_count": 10,
        }
    ]
    cache.create("statstest", papers=papers)
    # Act
    stats = cache.stats("statstest")
    # Assert
    assert stats["year_range"]["min"] == 2020


def test_stats_counts_papers_with_abstract(temp_cache_dir):
    # Arrange
    papers = [
        {
            "doi": "10.1234/test",
            "year": 2020,
            "journal": "Test Journal",
            "abstract": "Abstract text",
            "citation_count": 10,
        }
    ]
    cache.create("statstest", papers=papers)
    # Act
    stats = cache.stats("statstest")
    # Assert
    assert stats["with_abstract"] == 1


# ---------- delete / list ----------


def test_delete_removes_cache_from_disk(temp_cache_dir):
    # Arrange
    cache.create("deltest", papers=[{"doi": "10.1234/test"}])
    # Act
    cache.delete("deltest")
    # Assert
    assert not cache.exists("deltest")


def test_list_caches_returns_every_created_cache(temp_cache_dir):
    # Arrange
    cache.create("list1", papers=[{"doi": "10.1234/test"}])
    cache.create("list2", papers=[{"doi": "10.1234/test"}])
    # Act
    names = [c.name for c in cache.list_caches()]
    # Assert
    assert {"list1", "list2"}.issubset(names)


# ---------- export ----------


def test_export_to_json_writes_papers_array(temp_cache_dir, tmp_path):
    # Arrange
    cache.create(
        "exportjson",
        papers=[{"doi": "10.1234/test", "title": "Test", "year": 2020}],
    )
    out = tmp_path / "out.json"
    # Act
    cache.export("exportjson", str(out), format="json")
    # Assert
    assert json.loads(out.read_text())[0]["doi"] == "10.1234/test"


def test_export_to_dois_format_writes_one_doi_per_line(temp_cache_dir, tmp_path):
    # Arrange
    cache.create(
        "exportdois",
        papers=[{"doi": "10.1234/test1"}, {"doi": "10.1234/test2"}],
    )
    out = tmp_path / "out.txt"
    # Act
    cache.export("exportdois", str(out), format="dois")
    # Assert
    assert out.read_text().strip().split("\n") == ["10.1234/test1", "10.1234/test2"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
