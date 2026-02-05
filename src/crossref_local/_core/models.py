"""Data models for crossref_local."""

from dataclasses import dataclass as _dataclass
from dataclasses import field as _field
from typing import List, Optional

__all__ = [
    "Work",
    "SearchResult",
    "LimitInfo",
]


@_dataclass
class Work:
    """
    Represents a scholarly work from CrossRef.

    Attributes:
        doi: Digital Object Identifier
        title: Work title
        authors: List of author names
        year: Publication year
        journal: Journal/container title
        issn: Journal ISSN
        volume: Volume number
        issue: Issue number
        page: Page range
        publisher: Publisher name
        type: Work type (journal-article, book-chapter, etc.)
        abstract: Abstract text (if available)
        url: Resource URL
        citation_count: Number of citations (if available)
        references: List of reference DOIs
    """

    doi: str
    title: Optional[str] = None
    authors: List[str] = _field(default_factory=list)
    year: Optional[int] = None
    journal: Optional[str] = None
    issn: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    page: Optional[str] = None
    publisher: Optional[str] = None
    type: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[str] = None
    citation_count: Optional[int] = None
    references: List[str] = _field(default_factory=list)
    impact_factor: Optional[float] = None
    impact_factor_source: Optional[str] = None

    @classmethod
    def from_metadata(cls, doi: str, metadata: dict) -> "Work":
        """
        Create Work from CrossRef metadata JSON.

        Args:
            doi: DOI string
            metadata: CrossRef metadata dictionary

        Returns:
            Work instance
        """
        # Extract authors
        authors = []
        for author in metadata.get("author", []):
            given = author.get("given", "")
            family = author.get("family", "")
            if given and family:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)
            elif author.get("name"):
                authors.append(author["name"])

        # Extract year from published date
        year = None
        published = metadata.get("published", {})
        date_parts = published.get("date-parts", [[]])
        if date_parts and date_parts[0]:
            year = date_parts[0][0]

        # Extract references
        references = []
        for ref in metadata.get("reference", []):
            if ref.get("DOI"):
                references.append(ref["DOI"])

        # Container title (journal name)
        container_titles = metadata.get("container-title", [])
        journal = container_titles[0] if container_titles else None

        # ISSN
        issns = metadata.get("ISSN", [])
        issn = issns[0] if issns else None

        return cls(
            doi=doi,
            title=metadata.get("title", [None])[0] if metadata.get("title") else None,
            authors=authors,
            year=year,
            journal=journal,
            issn=issn,
            volume=metadata.get("volume"),
            issue=metadata.get("issue"),
            page=metadata.get("page"),
            publisher=metadata.get("publisher"),
            type=metadata.get("type"),
            abstract=metadata.get("abstract"),
            url=metadata.get("URL"),
            citation_count=metadata.get("is-referenced-by-count"),
            references=references,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "doi": self.doi,
            "title": self.title,
            "authors": self.authors,
            "year": self.year,
            "journal": self.journal,
            "issn": self.issn,
            "volume": self.volume,
            "issue": self.issue,
            "page": self.page,
            "publisher": self.publisher,
            "type": self.type,
            "abstract": self.abstract,
            "url": self.url,
            "citation_count": self.citation_count,
            "references": self.references,
            "impact_factor": round(self.impact_factor, 1)
            if self.impact_factor is not None
            else None,
            "impact_factor_source": self.impact_factor_source,
        }

    def citation(self, style: str = "apa") -> str:
        """
        Format as citation string.

        Args:
            style: Citation style (currently only "apa" supported)

        Returns:
            Formatted citation string
        """
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += " et al."

        year_str = f"({self.year})" if self.year else "(n.d.)"
        title_str = self.title or "Untitled"
        journal_str = f"*{self.journal}*" if self.journal else ""

        parts = [authors_str, year_str, title_str]
        if journal_str:
            parts.append(journal_str)
        if self.volume:
            parts.append(f"{self.volume}")
            if self.issue:
                parts[-1] += f"({self.issue})"
        if self.page:
            parts.append(self.page)
        parts.append(f"https://doi.org/{self.doi}")

        return ". ".join(filter(None, parts))

    def to_text(self, include_abstract: bool = False) -> str:
        """
        Format as human-readable text.

        Args:
            include_abstract: Include abstract in output

        Returns:
            Formatted text string
        """
        from .export import work_to_text

        return work_to_text(self, include_abstract=include_abstract)

    def to_bibtex(self) -> str:
        """
        Format as BibTeX entry.

        Returns:
            BibTeX string
        """
        from .export import work_to_bibtex

        return work_to_bibtex(self)

    def save(self, path: str, format: str = "json") -> str:
        """
        Save work to file.

        Args:
            path: Output file path
            format: Output format ("text", "json", "bibtex")

        Returns:
            Path to saved file

        Examples:
            >>> work = get("10.1038/nature12373")
            >>> work.save("paper.json")
            >>> work.save("paper.bib", format="bibtex")
        """
        from .export import save

        return save(self, path, format=format)


@_dataclass
class LimitInfo:
    """
    Information about result limiting at each stage.

    Attributes:
        requested: Number of results requested
        returned: Number of results actually returned
        total_available: Total matches in database
        capped: Whether results were capped
        capped_reason: Why results were capped (if applicable)
        stage: Which stage applied this limit (e.g., "crossref-local", "scitex", "django")
    """

    requested: int
    returned: int
    total_available: int
    capped: bool = False
    capped_reason: Optional[str] = None
    stage: str = "crossref-local"

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "requested": self.requested,
            "returned": self.returned,
            "total_available": self.total_available,
            "capped": self.capped,
            "capped_reason": self.capped_reason,
            "stage": self.stage,
        }


@_dataclass
class SearchResult:
    """
    Container for search results with metadata.

    Attributes:
        works: List of Work objects
        total: Total number of matches
        query: Original search query
        elapsed_ms: Search time in milliseconds
        limit_info: Information about result limiting
    """

    works: List[Work]
    total: int
    query: str
    elapsed_ms: float
    limit_info: Optional[LimitInfo] = None

    def __len__(self) -> int:
        return len(self.works)

    def __iter__(self):
        return iter(self.works)

    def __getitem__(self, idx):
        return self.works[idx]

    def save(
        self, path: str, format: str = "json", include_abstract: bool = True
    ) -> str:
        """
        Save search results to file.

        Args:
            path: Output file path
            format: Output format ("text", "json", "bibtex")
            include_abstract: Include abstracts in text format

        Returns:
            Path to saved file

        Examples:
            >>> results = search("machine learning", limit=10)
            >>> results.save("results.json")
            >>> results.save("results.bib", format="bibtex")
            >>> results.save("results.txt", format="text")
        """
        from .export import save

        return save(self, path, format=format, include_abstract=include_abstract)
