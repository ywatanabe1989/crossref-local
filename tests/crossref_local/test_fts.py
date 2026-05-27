"""Tests for crossref_local.fts module."""

import pytest

from crossref_local._core.fts import count, search, search_dois
from crossref_local._core.models import SearchResult, Work


# ---------- search() return shape ----------


def test_search_returns_search_result_instance():
    # Arrange
    # Act
    results = search("science", limit=1)
    # Assert
    assert isinstance(results, SearchResult)


def test_search_result_query_field_matches_supplied_query():
    # Arrange
    query = "biology"
    # Act
    results = search(query, limit=1)
    # Assert
    assert results.query == query


def test_search_result_total_is_integer_type():
    # Arrange
    # Act
    results = search("medicine", limit=1)
    # Assert
    assert isinstance(results.total, int)


def test_search_result_total_is_nonnegative():
    # Arrange
    # Act
    results = search("medicine", limit=1)
    # Assert
    assert results.total >= 0


def test_search_result_elapsed_ms_is_float_type():
    # Arrange
    # Act
    results = search("physics", limit=1)
    # Assert
    assert isinstance(results.elapsed_ms, float)


def test_search_result_elapsed_ms_is_nonnegative():
    # Arrange
    # Act
    results = search("physics", limit=1)
    # Assert
    assert results.elapsed_ms >= 0


def test_search_returns_work_objects_for_every_hit():
    # Arrange
    # Act
    results = search("chemistry", limit=3)
    # Assert
    assert all(isinstance(w, Work) for w in results.works)


def test_search_respects_limit_argument_for_returned_works():
    # Arrange
    limit = 5
    # Act
    results = search("cancer", limit=limit)
    # Assert
    assert len(results.works) <= limit


@pytest.fixture
def _neuroscience_paging():
    """Two-page neuroscience search, or skip when the fixture is too small."""
    page1 = search("neuroscience", limit=5, offset=0)
    if len(page1.works) < 5:
        pytest.skip("not enough hits to validate offset")
    page2 = search("neuroscience", limit=5, offset=5)
    if not page2.works:
        pytest.skip("offset page is empty in this fixture")
    return page1, page2


def test_search_with_offset_skips_already_returned_dois(_neuroscience_paging):
    # Arrange
    page1, page2 = _neuroscience_paging
    # Act
    same = page1.works[0].doi == page2.works[0].doi
    # Assert
    assert not same


def test_search_supports_fts5_quoted_phrase_syntax():
    # Arrange
    # Act
    results = search('"machine learning"', limit=5)
    # Assert
    assert isinstance(results, SearchResult)


def test_search_supports_fts5_boolean_and_operator():
    # Arrange
    # Act
    results = search("neural AND network", limit=5)
    # Assert
    assert isinstance(results, SearchResult)


# ---------- count() ----------


def test_count_returns_integer_type():
    # Arrange
    # Act
    n = count("biology")
    # Assert
    assert isinstance(n, int)


def test_count_returns_positive_for_common_term_in_fixture():
    # Arrange
    # Act
    n = count("cancer")
    # Assert
    assert n > 0


def test_count_returns_zero_for_nonsense_query_with_no_hits():
    # Arrange
    # Act
    n = count("xyzzy12345nonexistent")
    # Assert
    assert n == 0


def test_count_agrees_with_search_total_for_identical_query():
    # Arrange
    query = "quantum"
    # Act
    n = count(query)
    total = search(query, limit=1).total
    # Assert
    assert n == total


# ---------- search_dois() ----------


def test_search_dois_returns_list_instance():
    # Arrange
    # Act
    dois = search_dois("genetics", limit=10)
    # Assert
    assert isinstance(dois, list)


def test_search_dois_returns_only_string_values():
    # Arrange
    # Act
    dois = search_dois("genetics", limit=10)
    # Assert
    assert all(isinstance(d, str) for d in dois)


def test_search_dois_respects_limit_argument():
    # Arrange
    limit = 5
    # Act
    dois = search_dois("medicine", limit=limit)
    # Assert
    assert len(dois) <= limit


def test_search_dois_returns_only_valid_doi_prefix_strings():
    # Arrange
    # Act
    dois = search_dois("biology", limit=5)
    # Assert
    assert all(d.startswith("10.") for d in dois)


# ---------- FTS5 schema sanity ----------


def test_works_fts_virtual_table_exists_in_schema():
    # Arrange
    from crossref_local._core.db import get_db

    db = get_db()
    sql = (
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name='works_fts'"
    )
    # Act
    row = db.fetchone(sql)
    # Assert
    assert row is not None


def test_fts_search_returns_within_5_seconds_for_common_term():
    # Arrange
    # Act
    results = search("CRISPR", limit=10)
    # Assert
    assert results.elapsed_ms < 5000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
