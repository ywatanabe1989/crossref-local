"""Tests for crossref_local.models module."""

import pytest
from crossref_local.models import Work, SearchResult


class TestWork:
    """Tests for Work dataclass."""

    def test_work_creation(self):
        """Work can be created with minimal args."""
        work = Work(doi="10.1234/test")
        assert work.doi == "10.1234/test"

    def test_work_from_metadata(self):
        """Work.from_metadata creates Work from CrossRef JSON."""
        metadata = {
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
        work = Work.from_metadata("10.1234/test", metadata)

        assert work.doi == "10.1234/test"
        assert work.title == "Test Title"
        assert work.authors == ["John Doe", "Jane Smith"]
        assert work.year == 2023
        assert work.journal == "Test Journal"
        assert work.issn == "1234-5678"
        assert work.volume == "10"
        assert work.issue == "2"
        assert work.page == "100-110"
        assert work.publisher == "Test Publisher"
        assert work.type == "journal-article"
        assert work.citation_count == 42
        assert len(work.references) == 2

    def test_work_to_dict(self):
        """Work.to_dict returns dictionary."""
        work = Work(
            doi="10.1234/test",
            title="Test Title",
            year=2023,
        )
        d = work.to_dict()
        assert isinstance(d, dict)
        assert d["doi"] == "10.1234/test"
        assert d["title"] == "Test Title"
        assert d["year"] == 2023

    def test_work_citation(self):
        """Work.citation returns formatted citation."""
        work = Work(
            doi="10.1234/test",
            title="Test Title",
            authors=["John Doe", "Jane Smith"],
            year=2023,
            journal="Test Journal",
            volume="10",
            issue="2",
            page="100-110",
        )
        citation = work.citation()
        assert "John Doe" in citation
        assert "2023" in citation
        assert "Test Title" in citation
        assert "10.1234/test" in citation


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_length(self):
        """SearchResult len() returns number of works."""
        works = [Work(doi=f"10.1234/{i}") for i in range(5)]
        result = SearchResult(works=works, total=100, query="test", elapsed_ms=10.0)
        assert len(result) == 5

    def test_search_result_iteration(self):
        """SearchResult is iterable."""
        works = [Work(doi=f"10.1234/{i}") for i in range(3)]
        result = SearchResult(works=works, total=100, query="test", elapsed_ms=10.0)
        dois = [w.doi for w in result]
        assert dois == ["10.1234/0", "10.1234/1", "10.1234/2"]

    def test_search_result_indexing(self):
        """SearchResult supports indexing."""
        works = [Work(doi=f"10.1234/{i}") for i in range(3)]
        result = SearchResult(works=works, total=100, query="test", elapsed_ms=10.0)
        assert result[0].doi == "10.1234/0"
        assert result[-1].doi == "10.1234/2"


if __name__ == "__main__":
    import os
    import pytest
    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/crossref_local/src/crossref_local/models.py
# --------------------------------------------------------------------------------
# """Data models for crossref_local."""
# 
# from dataclasses import dataclass, field
# from typing import List, Optional
# import json
# 
# 
# @dataclass
# class Work:
#     """
#     Represents a scholarly work from CrossRef.
# 
#     Attributes:
#         doi: Digital Object Identifier
#         title: Work title
#         authors: List of author names
#         year: Publication year
#         journal: Journal/container title
#         issn: Journal ISSN
#         volume: Volume number
#         issue: Issue number
#         page: Page range
#         publisher: Publisher name
#         type: Work type (journal-article, book-chapter, etc.)
#         abstract: Abstract text (if available)
#         url: Resource URL
#         citation_count: Number of citations (if available)
#         references: List of reference DOIs
#     """
# 
#     doi: str
#     title: Optional[str] = None
#     authors: List[str] = field(default_factory=list)
#     year: Optional[int] = None
#     journal: Optional[str] = None
#     issn: Optional[str] = None
#     volume: Optional[str] = None
#     issue: Optional[str] = None
#     page: Optional[str] = None
#     publisher: Optional[str] = None
#     type: Optional[str] = None
#     abstract: Optional[str] = None
#     url: Optional[str] = None
#     citation_count: Optional[int] = None
#     references: List[str] = field(default_factory=list)
# 
#     @classmethod
#     def from_metadata(cls, doi: str, metadata: dict) -> "Work":
#         """
#         Create Work from CrossRef metadata JSON.
# 
#         Args:
#             doi: DOI string
#             metadata: CrossRef metadata dictionary
# 
#         Returns:
#             Work instance
#         """
#         # Extract authors
#         authors = []
#         for author in metadata.get("author", []):
#             given = author.get("given", "")
#             family = author.get("family", "")
#             if given and family:
#                 authors.append(f"{given} {family}")
#             elif family:
#                 authors.append(family)
#             elif author.get("name"):
#                 authors.append(author["name"])
# 
#         # Extract year from published date
#         year = None
#         published = metadata.get("published", {})
#         date_parts = published.get("date-parts", [[]])
#         if date_parts and date_parts[0]:
#             year = date_parts[0][0]
# 
#         # Extract references
#         references = []
#         for ref in metadata.get("reference", []):
#             if ref.get("DOI"):
#                 references.append(ref["DOI"])
# 
#         # Container title (journal name)
#         container_titles = metadata.get("container-title", [])
#         journal = container_titles[0] if container_titles else None
# 
#         # ISSN
#         issns = metadata.get("ISSN", [])
#         issn = issns[0] if issns else None
# 
#         return cls(
#             doi=doi,
#             title=metadata.get("title", [None])[0] if metadata.get("title") else None,
#             authors=authors,
#             year=year,
#             journal=journal,
#             issn=issn,
#             volume=metadata.get("volume"),
#             issue=metadata.get("issue"),
#             page=metadata.get("page"),
#             publisher=metadata.get("publisher"),
#             type=metadata.get("type"),
#             abstract=metadata.get("abstract"),
#             url=metadata.get("URL"),
#             citation_count=metadata.get("is-referenced-by-count"),
#             references=references,
#         )
# 
#     def to_dict(self) -> dict:
#         """Convert to dictionary."""
#         return {
#             "doi": self.doi,
#             "title": self.title,
#             "authors": self.authors,
#             "year": self.year,
#             "journal": self.journal,
#             "issn": self.issn,
#             "volume": self.volume,
#             "issue": self.issue,
#             "page": self.page,
#             "publisher": self.publisher,
#             "type": self.type,
#             "abstract": self.abstract,
#             "url": self.url,
#             "citation_count": self.citation_count,
#             "references": self.references,
#         }
# 
#     def citation(self, style: str = "apa") -> str:
#         """
#         Format as citation string.
# 
#         Args:
#             style: Citation style (currently only "apa" supported)
# 
#         Returns:
#             Formatted citation string
#         """
#         authors_str = ", ".join(self.authors[:3])
#         if len(self.authors) > 3:
#             authors_str += " et al."
# 
#         year_str = f"({self.year})" if self.year else "(n.d.)"
#         title_str = self.title or "Untitled"
#         journal_str = f"*{self.journal}*" if self.journal else ""
# 
#         parts = [authors_str, year_str, title_str]
#         if journal_str:
#             parts.append(journal_str)
#         if self.volume:
#             parts.append(f"{self.volume}")
#             if self.issue:
#                 parts[-1] += f"({self.issue})"
#         if self.page:
#             parts.append(self.page)
#         parts.append(f"https://doi.org/{self.doi}")
# 
#         return ". ".join(filter(None, parts))
# 
# 
# @dataclass
# class SearchResult:
#     """
#     Container for search results with metadata.
# 
#     Attributes:
#         works: List of Work objects
#         total: Total number of matches
#         query: Original search query
#         elapsed_ms: Search time in milliseconds
#     """
# 
#     works: List[Work]
#     total: int
#     query: str
#     elapsed_ms: float
# 
#     def __len__(self) -> int:
#         return len(self.works)
# 
#     def __iter__(self):
#         return iter(self.works)
# 
#     def __getitem__(self, idx):
#         return self.works[idx]

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/crossref_local/src/crossref_local/models.py
# --------------------------------------------------------------------------------
