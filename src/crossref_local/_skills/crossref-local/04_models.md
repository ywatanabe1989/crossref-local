---
package: crossref-local
skill: models
---

# Data Models

## `Work` Dataclass

Represents a single scholarly work from CrossRef.

```python
@dataclass
class Work:
    doi: str
    title: Optional[str] = None
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    journal: Optional[str] = None
    issn: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    page: Optional[str] = None
    publisher: Optional[str] = None
    type: Optional[str] = None          # "journal-article", "book-chapter", etc.
    abstract: Optional[str] = None
    url: Optional[str] = None
    citation_count: Optional[int] = None
    references: List[str] = field(default_factory=list)  # list of DOIs
    impact_factor: Optional[float] = None
    impact_factor_source: Optional[str] = None
```

### Work Methods

| Method | Signature | Returns |
|--------|-----------|---------|
| `to_dict()` | `() -> dict` | All fields as dict |
| `to_text()` | `(include_abstract: bool = False) -> str` | Human-readable text |
| `to_bibtex()` | `() -> str` | BibTeX entry string |
| `citation()` | `(style: str = "apa") -> str` | Formatted APA citation |
| `save()` | `(path: str, format: str = "json") -> str` | Path to saved file |
| `from_metadata()` | `(doi, metadata: dict) -> Work` | classmethod from raw CrossRef JSON |

### Work Examples

```python
work = crl.get("10.1038/nature12373")

# Format as citation
print(work.citation())
# -> "Malenka R, ..., (2013). ..."

# Convert to dict
d = work.to_dict()
# Keys: doi, title, authors, year, journal, issn, volume, issue,
#       page, publisher, type, abstract, url, citation_count,
#       references, impact_factor, impact_factor_source

# Format as BibTeX
bib = work.to_bibtex()

# Save to files
work.save("paper.json")
work.save("paper.bib", format="bibtex")
work.save("paper.txt", format="text")

# Human-readable
print(work.to_text(include_abstract=True))
```

### CrossRef Work Types

| CrossRef type | BibTeX type |
|--------------|-------------|
| `journal-article` | `article` |
| `book-chapter` | `incollection` |
| `book` | `book` |
| `proceedings-article` | `inproceedings` |
| `dissertation` | `phdthesis` |
| `report` | `techreport` |
| (other) | `misc` |

## `SearchResult` Dataclass

Container returned by `search()`.

```python
@dataclass
class SearchResult:
    works: List[Work]
    total: int         # total matches (may exceed len(works))
    query: str         # original query string
    elapsed_ms: float  # search duration in milliseconds
    limit_info: Optional[LimitInfo] = None
```

### SearchResult Methods

| Method | Signature | Returns |
|--------|-----------|---------|
| `__len__()` | `() -> int` | `len(works)` |
| `__iter__()` | | iterates over works |
| `__getitem__()` | `(idx)` | `works[idx]` |
| `save()` | `(path, format="json", include_abstract=True) -> str` | Path to file |

```python
results = crl.search("CRISPR", limit=20)
print(len(results))          # 20 (returned)
print(results.total)         # potentially millions
print(results.elapsed_ms)    # e.g., 12.3

# Iterate
for work in results:
    print(work.doi)

# Index
first = results[0]

# Save
results.save("results.json")
results.save("results.bib", format="bibtex")
results.save("results.txt", format="text", include_abstract=False)
```

## `LimitInfo` Dataclass

Metadata about result limiting (useful in layered deployments).

```python
@dataclass
class LimitInfo:
    requested: int
    returned: int
    total_available: int
    capped: bool = False
    capped_reason: Optional[str] = None
    stage: str = "crossref-local"
```
