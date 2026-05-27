"""Tests for crossref_local.models module."""

import pytest

from crossref_local._core.models import SearchResult, Work


# ---------- Work construction & from_metadata ----------


def test_work_constructor_stores_doi_with_minimal_args():
    # Arrange
    doi = "10.1234/test"
    # Act
    work = Work(doi=doi)
    # Assert
    assert work.doi == doi


@pytest.fixture
def _full_metadata():
    """A representative CrossRef metadata payload used across from_metadata tests."""
    return {
        "title": ["Test Title"],
        "author": [
            {"given": "John", "family": "Doe"},
            {"given": "Jane", "family": "Smith"},
        ],
        "published": {"date-parts": [[2023]]},
        "container-title": ["Test Journal"],
        "ISSN": ["1234-5678"],
        "volume": "10",
        "issue": "2",
        "page": "100-110",
        "publisher": "Test Publisher",
        "type": "journal-article",
        "is-referenced-by-count": 42,
        "reference": [
            {"DOI": "10.1111/ref1"},
            {"DOI": "10.2222/ref2"},
        ],
    }


def test_work_from_metadata_carries_supplied_doi(_full_metadata):
    # Arrange
    doi = "10.1234/test"
    # Act
    work = Work.from_metadata(doi, _full_metadata)
    # Assert
    assert work.doi == doi


def test_work_from_metadata_extracts_first_title(_full_metadata):
    # Arrange
    # Act
    work = Work.from_metadata("10.1234/test", _full_metadata)
    # Assert
    assert work.title == "Test Title"


def test_work_from_metadata_joins_given_and_family_for_each_author(_full_metadata):
    # Arrange
    # Act
    work = Work.from_metadata("10.1234/test", _full_metadata)
    # Assert
    assert work.authors == ["John Doe", "Jane Smith"]


def test_work_from_metadata_pulls_year_from_published_date_parts(_full_metadata):
    # Arrange
    # Act
    work = Work.from_metadata("10.1234/test", _full_metadata)
    # Assert
    assert work.year == 2023


def test_work_from_metadata_takes_first_container_title_as_journal(_full_metadata):
    # Arrange
    # Act
    work = Work.from_metadata("10.1234/test", _full_metadata)
    # Assert
    assert work.journal == "Test Journal"


def test_work_from_metadata_takes_first_issn(_full_metadata):
    # Arrange
    # Act
    work = Work.from_metadata("10.1234/test", _full_metadata)
    # Assert
    assert work.issn == "1234-5678"


def test_work_from_metadata_preserves_volume(_full_metadata):
    # Arrange
    # Act
    work = Work.from_metadata("10.1234/test", _full_metadata)
    # Assert
    assert work.volume == "10"


def test_work_from_metadata_preserves_issue(_full_metadata):
    # Arrange
    # Act
    work = Work.from_metadata("10.1234/test", _full_metadata)
    # Assert
    assert work.issue == "2"


def test_work_from_metadata_preserves_page_range(_full_metadata):
    # Arrange
    # Act
    work = Work.from_metadata("10.1234/test", _full_metadata)
    # Assert
    assert work.page == "100-110"


def test_work_from_metadata_preserves_publisher(_full_metadata):
    # Arrange
    # Act
    work = Work.from_metadata("10.1234/test", _full_metadata)
    # Assert
    assert work.publisher == "Test Publisher"


def test_work_from_metadata_preserves_type(_full_metadata):
    # Arrange
    # Act
    work = Work.from_metadata("10.1234/test", _full_metadata)
    # Assert
    assert work.type == "journal-article"


def test_work_from_metadata_extracts_citation_count_from_referenced_by(_full_metadata):
    # Arrange
    # Act
    work = Work.from_metadata("10.1234/test", _full_metadata)
    # Assert
    assert work.citation_count == 42


def test_work_from_metadata_collects_reference_dois(_full_metadata):
    # Arrange
    # Act
    work = Work.from_metadata("10.1234/test", _full_metadata)
    # Assert
    assert work.references == ["10.1111/ref1", "10.2222/ref2"]


# ---------- Work.to_dict ----------


@pytest.fixture
def _simple_work():
    return Work(doi="10.1234/test", title="Test Title", year=2023)


def test_work_to_dict_returns_dict_instance(_simple_work):
    # Arrange
    # Act
    d = _simple_work.to_dict()
    # Assert
    assert isinstance(d, dict)


def test_work_to_dict_serialises_doi(_simple_work):
    # Arrange
    # Act
    d = _simple_work.to_dict()
    # Assert
    assert d["doi"] == "10.1234/test"


def test_work_to_dict_serialises_title(_simple_work):
    # Arrange
    # Act
    d = _simple_work.to_dict()
    # Assert
    assert d["title"] == "Test Title"


def test_work_to_dict_serialises_year(_simple_work):
    # Arrange
    # Act
    d = _simple_work.to_dict()
    # Assert
    assert d["year"] == 2023


# ---------- Work.citation ----------


@pytest.fixture
def _citation_work():
    return Work(
        doi="10.1234/test",
        title="Test Title",
        authors=["John Doe", "Jane Smith"],
        year=2023,
        journal="Test Journal",
        volume="10",
        issue="2",
        page="100-110",
    )


def test_work_citation_includes_first_author_surname(_citation_work):
    # Arrange
    # Act
    citation = _citation_work.citation()
    # Assert
    assert "John Doe" in citation


def test_work_citation_includes_year(_citation_work):
    # Arrange
    # Act
    citation = _citation_work.citation()
    # Assert
    assert "2023" in citation


def test_work_citation_includes_title(_citation_work):
    # Arrange
    # Act
    citation = _citation_work.citation()
    # Assert
    assert "Test Title" in citation


def test_work_citation_includes_doi(_citation_work):
    # Arrange
    # Act
    citation = _citation_work.citation()
    # Assert
    assert "10.1234/test" in citation


# ---------- SearchResult container ----------


@pytest.fixture
def _five_work_result():
    works = [Work(doi=f"10.1234/{i}") for i in range(5)]
    return SearchResult(works=works, total=100, query="test", elapsed_ms=10.0)


@pytest.fixture
def _three_work_result():
    works = [Work(doi=f"10.1234/{i}") for i in range(3)]
    return SearchResult(works=works, total=100, query="test", elapsed_ms=10.0)


def test_search_result_len_returns_number_of_works(_five_work_result):
    # Arrange
    # Act
    n = len(_five_work_result)
    # Assert
    assert n == 5


def test_search_result_iteration_yields_dois_in_order(_three_work_result):
    # Arrange
    # Act
    dois = [w.doi for w in _three_work_result]
    # Assert
    assert dois == ["10.1234/0", "10.1234/1", "10.1234/2"]


def test_search_result_indexing_returns_work_at_position_zero(_three_work_result):
    # Arrange
    # Act
    first = _three_work_result[0]
    # Assert
    assert first.doi == "10.1234/0"


def test_search_result_indexing_supports_negative_index(_three_work_result):
    # Arrange
    # Act
    last = _three_work_result[-1]
    # Assert
    assert last.doi == "10.1234/2"


if __name__ == "__main__":
    import os

    pytest.main([os.path.abspath(__file__)])
