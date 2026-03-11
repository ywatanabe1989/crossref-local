"""Citation checking and validation against the local database."""

import json
import re
import time
from dataclasses import dataclass as _dataclass
from dataclasses import field as _field
from pathlib import Path
from typing import Iterator, List, Optional, Union

from .models import Work

__all__ = [
    "CitationEntry",
    "CheckResult",
    "check_citations",
    "check_bibtex",
    "check_doi_list",
]


@_dataclass
class CitationEntry:
    """A single citation check result."""

    identifier: str
    source_key: Optional[str] = None
    title: Optional[str] = None
    found: bool = False
    work: Optional[Work] = None
    issues: List[str] = _field(default_factory=list)
    suggestions: List[str] = _field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "identifier": self.identifier,
            "source_key": self.source_key,
            "title": self.title,
            "found": self.found,
            "issues": self.issues,
            "suggestions": self.suggestions,
        }


@_dataclass
class CheckResult:
    """Results from bulk citation checking."""

    entries: List[CitationEntry]
    total: int
    found: int
    missing: int
    with_issues: int
    elapsed_ms: float

    def __len__(self) -> int:
        return self.total

    def __iter__(self) -> Iterator[CitationEntry]:
        return iter(self.entries)

    def to_dict(self) -> dict:
        return {
            "summary": {
                "total": self.total,
                "found": self.found,
                "missing": self.missing,
                "with_issues": self.with_issues,
                "elapsed_ms": round(self.elapsed_ms, 2),
            },
            "entries": [e.to_dict() for e in self.entries],
        }

    def save(self, path: Union[str, Path], format: str = "json") -> str:
        path = Path(path)
        if format == "json":
            content = json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
        elif format == "text":
            content = self._format_text()
        else:
            raise ValueError(f"Unsupported format: {format}")
        path.write_text(content, encoding="utf-8")
        return str(path)

    def _format_text(self) -> str:
        lines = []
        lines.append("Citation Check Results")
        lines.append("=" * 50)
        lines.append(f"Total:       {self.total}")
        lines.append(
            f"Found:       {self.found} ({self.found / max(self.total, 1) * 100:.1f}%)"
        )
        lines.append(
            f"Missing:     {self.missing} ({self.missing / max(self.total, 1) * 100:.1f}%)"
        )
        lines.append(f"With issues: {self.with_issues}")
        lines.append(f"Time:        {self.elapsed_ms:.1f}ms")
        lines.append("")

        missing = [e for e in self.entries if not e.found]
        if missing:
            lines.append("Missing Citations:")
            for e in missing:
                key = f" ({e.source_key})" if e.source_key else ""
                lines.append(f"  - {e.identifier}{key}")
                for issue in e.issues:
                    lines.append(f"    {issue}")
            lines.append("")

        with_issues = [e for e in self.entries if e.found and e.issues]
        if with_issues:
            lines.append("Found with Issues:")
            for e in with_issues:
                key = f" ({e.source_key})" if e.source_key else ""
                lines.append(f"  - {e.identifier}{key}")
                for issue in e.issues:
                    lines.append(f"    ! {issue}")
                for sug in e.suggestions:
                    lines.append(f"    > {sug}")
            lines.append("")

        return "\n".join(lines)


def check_citations(
    identifiers: List[str],
    source_keys: Optional[List[str]] = None,
    titles: Optional[List[str]] = None,
    validate_metadata: bool = True,
    suggest_enrichment: bool = True,
) -> CheckResult:
    """Check citations against the local CrossRef database.

    Args:
        identifiers: List of DOIs to check
        source_keys: Optional list of source keys (e.g., BibTeX keys)
        titles: Optional list of titles
        validate_metadata: Check for incomplete metadata (default: True)
        suggest_enrichment: Suggest metadata improvements (default: True)

    Returns:
        CheckResult with summary and per-entry details

    Examples:
        >>> result = check_citations(["10.1038/nature12373", "10.1126/science.aax0758"])
        >>> print(f"Found: {result.found}/{result.total}")
        >>> result.save("check_results.json")
    """
    from .. import get_many

    t0 = time.time()

    # Normalize DOIs
    normalized = [_normalize_doi(doi) for doi in identifiers]

    # Batch lookup
    works_map = {}
    works = get_many([d for d in normalized if d])
    for w in works:
        works_map[w.doi.lower()] = w

    entries = []
    found_count = 0
    issue_count = 0

    for i, doi in enumerate(normalized):
        key = source_keys[i] if source_keys and i < len(source_keys) else None
        title = titles[i] if titles and i < len(titles) else None

        entry = CitationEntry(identifier=identifiers[i], source_key=key, title=title)

        if not doi:
            entry.issues.append("No valid DOI found")
            entries.append(entry)
            issue_count += 1
            continue

        work = works_map.get(doi.lower())
        if work:
            entry.found = True
            entry.work = work
            found_count += 1

            if validate_metadata:
                issues, suggestions = _validate_metadata(work)
                entry.issues = issues
                entry.suggestions = suggestions
                if issues:
                    issue_count += 1
        else:
            entry.issues.append("DOI not found in database")
            if suggest_enrichment:
                entry.suggestions.append("Verify DOI is correct")

        entries.append(entry)

    elapsed = (time.time() - t0) * 1000

    return CheckResult(
        entries=entries,
        total=len(entries),
        found=found_count,
        missing=len(entries) - found_count,
        with_issues=issue_count,
        elapsed_ms=elapsed,
    )


def check_bibtex(
    bib_path: Union[str, Path],
    validate_metadata: bool = True,
    suggest_enrichment: bool = True,
) -> CheckResult:
    """Check all citations in a BibTeX file against the local database.

    Args:
        bib_path: Path to BibTeX file
        validate_metadata: Check for incomplete metadata (default: True)
        suggest_enrichment: Suggest metadata improvements (default: True)

    Returns:
        CheckResult with summary and per-entry details including source_key

    Examples:
        >>> result = check_bibtex("bibliography.bib")
        >>> result.save("check_results.json")
        >>> for entry in result:
        ...     if not entry.found:
        ...         print(f"Missing: {entry.source_key} - {entry.identifier}")
    """
    path = Path(bib_path)
    if not path.exists():
        raise FileNotFoundError(f"BibTeX file not found: {path}")

    try:
        import bibtexparser
    except ImportError:
        raise ImportError(
            "bibtexparser is required for BibTeX parsing. Install with:\n"
            "  pip install bibtexparser"
        )

    with open(path, encoding="utf-8") as f:
        bib_db = bibtexparser.load(f)

    identifiers = []
    source_keys = []
    titles = []

    for entry in bib_db.entries:
        key = entry.get("ID", "")
        title = entry.get("title", "")
        doi = _extract_doi(entry)
        identifiers.append(doi or "")
        source_keys.append(key)
        titles.append(title)

    return check_citations(
        identifiers=identifiers,
        source_keys=source_keys,
        titles=titles,
        validate_metadata=validate_metadata,
        suggest_enrichment=suggest_enrichment,
    )


def check_doi_list(
    list_path: Union[str, Path],
    validate_metadata: bool = True,
    suggest_enrichment: bool = True,
) -> CheckResult:
    """Check all DOIs in a list file against the local database.

    Args:
        list_path: Path to file with DOIs (one per line or comma-separated)
        validate_metadata: Check for incomplete metadata (default: True)
        suggest_enrichment: Suggest metadata improvements (default: True)

    Returns:
        CheckResult with summary and per-entry details

    Examples:
        >>> result = check_doi_list("dois.txt")
        >>> print(result.to_dict())
    """
    path = Path(list_path)
    if not path.exists():
        raise FileNotFoundError(f"DOI list file not found: {path}")

    content = path.read_text(encoding="utf-8")
    raw = re.split(r"[,\n]", content)
    dois = []
    for item in raw:
        item = item.strip()
        if not item or item.startswith("#"):
            continue
        dois.append(item)

    return check_citations(
        identifiers=dois,
        validate_metadata=validate_metadata,
        suggest_enrichment=suggest_enrichment,
    )


def _normalize_doi(doi: str) -> str:
    """Strip URL prefix and normalize DOI."""
    doi = doi.strip()
    doi = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    return doi


def _extract_doi(entry: dict) -> Optional[str]:
    """Extract DOI from BibTeX entry dict."""
    doi = entry.get("doi", "")
    if doi:
        return _normalize_doi(doi)
    url = entry.get("url", "")
    m = re.search(r"doi\.org/(.+?)(?:\s|$)", url)
    if m:
        return _normalize_doi(m.group(1))
    return None


def _validate_metadata(work: Work) -> tuple:
    """Check Work for issues and return (issues, suggestions)."""
    issues = []
    suggestions = []
    if not work.abstract:
        issues.append("Missing abstract in database")
        suggestions.append("Abstract may not be available from CrossRef for this work")
    if not work.authors:
        issues.append("Missing author list")
    if not work.year:
        issues.append("Missing publication year")
    return issues, suggestions
