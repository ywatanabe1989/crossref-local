"""Export functionality for Work and SearchResult objects.

Supports multiple output formats:
- text: Human-readable formatted text
- json: JSON format with all fields
- bibtex: BibTeX bibliography format
"""

import json as _json
from pathlib import Path as _Path
from typing import TYPE_CHECKING, List, Optional, Union

if TYPE_CHECKING:
    from .models import SearchResult, Work

__all__ = [
    "save",
    "export_text",
    "export_json",
    "export_bibtex",
    "SUPPORTED_FORMATS",
]

SUPPORTED_FORMATS = ["text", "json", "bibtex"]


def _sanitize_bibtex_key(doi: str) -> str:
    """Convert DOI to valid BibTeX key."""
    return doi.replace("/", "_").replace(".", "_").replace("-", "_")


def _escape_bibtex(text: str) -> str:
    """Escape special characters for BibTeX."""
    if not text:
        return ""
    # Escape special LaTeX characters
    replacements = [
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
    ]
    for old, new in replacements:
        text = text.replace(old, new)
    return text


def work_to_text(work: "Work", include_abstract: bool = False) -> str:
    """Convert a Work to human-readable text format.

    Args:
        work: Work object to convert
        include_abstract: Whether to include abstract

    Returns:
        Formatted text string
    """
    lines = []

    # Title
    title = work.title or "Untitled"
    year = f"({work.year})" if work.year else ""
    lines.append(f"{title} {year}".strip())

    # Authors
    if work.authors:
        authors_str = ", ".join(work.authors[:5])
        if len(work.authors) > 5:
            authors_str += f" et al. ({len(work.authors)} authors)"
        lines.append(f"Authors: {authors_str}")

    # Journal and DOI
    if work.journal:
        journal_line = f"Journal: {work.journal}"
        if work.volume:
            journal_line += f", {work.volume}"
            if work.issue:
                journal_line += f"({work.issue})"
        if work.page:
            journal_line += f", {work.page}"
        lines.append(journal_line)

    lines.append(f"DOI: {work.doi}")

    # Impact factor
    if work.impact_factor:
        lines.append(
            f"Impact Factor: {work.impact_factor:.2f} ({work.impact_factor_source or 'unknown'})"
        )

    # Citation count
    if work.citation_count is not None:
        lines.append(f"Citations: {work.citation_count}")

    # Abstract
    if include_abstract and work.abstract:
        # Strip XML tags
        import re

        abstract = re.sub(r"<[^>]+>", " ", work.abstract)
        abstract = re.sub(r"\s+", " ", abstract).strip()
        lines.append(f"Abstract: {abstract}")

    return "\n".join(lines)


def work_to_bibtex(work: "Work") -> str:
    """Convert a Work to BibTeX format.

    Args:
        work: Work object to convert

    Returns:
        BibTeX entry string
    """
    key = _sanitize_bibtex_key(work.doi) if work.doi else "unknown"
    work_type = work.type or "article"

    # Map CrossRef types to BibTeX types
    bibtex_type_map = {
        "journal-article": "article",
        "book-chapter": "incollection",
        "book": "book",
        "proceedings-article": "inproceedings",
        "dissertation": "phdthesis",
        "report": "techreport",
    }
    bibtex_type = bibtex_type_map.get(work_type, "misc")

    lines = [f"@{bibtex_type}{{{key},"]

    if work.title:
        lines.append(f"  title = {{{_escape_bibtex(work.title)}}},")

    if work.authors:
        authors = " and ".join(work.authors)
        lines.append(f"  author = {{{_escape_bibtex(authors)}}},")

    if work.year:
        lines.append(f"  year = {{{work.year}}},")

    if work.journal:
        lines.append(f"  journal = {{{_escape_bibtex(work.journal)}}},")

    if work.volume:
        lines.append(f"  volume = {{{work.volume}}},")

    if work.issue:
        lines.append(f"  number = {{{work.issue}}},")

    if work.page:
        lines.append(f"  pages = {{{work.page}}},")

    if work.publisher:
        lines.append(f"  publisher = {{{_escape_bibtex(work.publisher)}}},")

    if work.doi:
        lines.append(f"  doi = {{{work.doi}}},")

    if work.url:
        lines.append(f"  url = {{{work.url}}},")

    if work.issn:
        lines.append(f"  issn = {{{work.issn}}},")

    lines.append("}")

    return "\n".join(lines)


def export_text(
    works: List["Work"],
    include_abstract: bool = False,
    query: Optional[str] = None,
    total: Optional[int] = None,
    elapsed_ms: Optional[float] = None,
) -> str:
    """Export works to text format.

    Args:
        works: List of Work objects
        include_abstract: Whether to include abstracts
        query: Original search query (for header)
        total: Total number of matches
        elapsed_ms: Search time in milliseconds

    Returns:
        Formatted text string
    """
    lines = []

    # Header
    if query is not None:
        lines.append(f"Search: {query}")
        if total is not None:
            lines.append(f"Found: {total:,} matches")
        if elapsed_ms is not None:
            lines.append(f"Time: {elapsed_ms:.1f}ms")
        lines.append("")
        lines.append("=" * 60)
        lines.append("")

    # Works
    for i, work in enumerate(works, 1):
        lines.append(f"[{i}]")
        lines.append(work_to_text(work, include_abstract=include_abstract))
        lines.append("")
        lines.append("-" * 40)
        lines.append("")

    return "\n".join(lines)


def export_json(
    works: List["Work"],
    query: Optional[str] = None,
    total: Optional[int] = None,
    elapsed_ms: Optional[float] = None,
    indent: int = 2,
) -> str:
    """Export works to JSON format.

    Args:
        works: List of Work objects
        query: Original search query
        total: Total number of matches
        elapsed_ms: Search time in milliseconds
        indent: JSON indentation

    Returns:
        JSON string
    """
    data = {
        "works": [w.to_dict() for w in works],
    }

    if query is not None:
        data["query"] = query
    if total is not None:
        data["total"] = total
    if elapsed_ms is not None:
        data["elapsed_ms"] = elapsed_ms

    return _json.dumps(data, indent=indent, ensure_ascii=False)


def export_bibtex(works: List["Work"]) -> str:
    """Export works to BibTeX format.

    Args:
        works: List of Work objects

    Returns:
        BibTeX string with all entries
    """
    entries = [work_to_bibtex(w) for w in works]
    return "\n\n".join(entries)


def save(
    data: Union["Work", "SearchResult", List["Work"]],
    path: Union[str, _Path],
    format: str = "json",
    include_abstract: bool = True,
) -> str:
    """Save Work(s) or SearchResult to a file.

    Args:
        data: Work, SearchResult, or list of Works to save
        path: Output file path
        format: Output format ("text", "json", "bibtex")
        include_abstract: Include abstracts in text format

    Returns:
        Path to saved file

    Raises:
        ValueError: If format is not supported

    Examples:
        >>> from crossref_local import search, save
        >>> results = search("machine learning", limit=10)
        >>> save(results, "results.json")
        >>> save(results, "results.bib", format="bibtex")
        >>> save(results, "results.txt", format="text")
    """
    from .models import SearchResult, Work

    if format not in SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format: {format}. "
            f"Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )

    path = _Path(path)

    # Extract works and metadata
    if isinstance(data, Work):
        works = [data]
        query = None
        total = None
        elapsed_ms = None
    elif isinstance(data, SearchResult):
        works = data.works
        query = data.query
        total = data.total
        elapsed_ms = data.elapsed_ms
    elif isinstance(data, list):
        works = data
        query = None
        total = len(data)
        elapsed_ms = None
    else:
        raise TypeError(f"Unsupported data type: {type(data)}")

    # Generate content
    if format == "text":
        content = export_text(
            works,
            include_abstract=include_abstract,
            query=query,
            total=total,
            elapsed_ms=elapsed_ms,
        )
    elif format == "json":
        content = export_json(
            works,
            query=query,
            total=total,
            elapsed_ms=elapsed_ms,
        )
    elif format == "bibtex":
        content = export_bibtex(works)
    else:
        raise ValueError(f"Unsupported format: {format}")

    # Write to file
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    return str(path)
