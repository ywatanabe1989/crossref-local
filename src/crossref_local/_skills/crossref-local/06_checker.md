---
package: crossref-local
skill: checker
---

# Citation Checker

Validate that DOIs exist in the local database and check metadata completeness.
Useful for proofreading BibTeX files and DOI lists before submission.

## Signatures

```python
check_citations(
    identifiers: list[str],
    source_keys: Optional[list[str]] = None,
    titles: Optional[list[str]] = None,
    validate_metadata: bool = True,
    suggest_enrichment: bool = True,
) -> CheckResult

check_bibtex(
    bib_path: str | Path,
    validate_metadata: bool = True,
    suggest_enrichment: bool = True,
) -> CheckResult

check_doi_list(
    list_path: str | Path,
    validate_metadata: bool = True,
    suggest_enrichment: bool = True,
) -> CheckResult
```

## `CheckResult` Dataclass

```python
@dataclass
class CheckResult:
    entries: List[CitationEntry]
    total: int
    found: int
    missing: int
    with_issues: int
    elapsed_ms: float

    def to_dict(self) -> dict
    def save(self, path: str | Path, format: str = "json") -> str
    # format: "json" or "text"
```

## `CitationEntry` Dataclass

```python
@dataclass
class CitationEntry:
    identifier: str            # original DOI string
    source_key: Optional[str]  # BibTeX key (if from .bib file)
    title: Optional[str]       # title from BibTeX (if available)
    found: bool                # True if DOI exists in DB
    work: Optional[Work]       # Work object if found
    issues: List[str]          # metadata issues (missing abstract, etc.)
    suggestions: List[str]     # improvement suggestions
```

## Examples

### Check a List of DOIs

```python
import crossref_local as crl

result = crl.check_citations([
    "10.1038/nature12373",
    "10.1126/science.aax0758",
    "10.xxxx/invalid-doi",
])
print(f"Found: {result.found}/{result.total}")

for entry in result:
    status = "OK" if entry.found else "MISSING"
    print(f"  [{status}] {entry.identifier}")
    for issue in entry.issues:
        print(f"    ! {issue}")
```

### Check BibTeX File

Requires `bibtexparser`: `pip install bibtexparser`

```python
result = crl.check_bibtex("bibliography.bib")
print(f"Found: {result.found}/{result.total}")

# Missing citations
missing = [e for e in result if not e.found]
for e in missing:
    print(f"  MISSING: {e.source_key} ({e.identifier})")

# Save report
result.save("check_report.json")
result.save("check_report.txt", format="text")
```

### Check DOI List File

Accepts one DOI per line, or comma-separated. Lines starting with `#` are
comments.

```
# dois.txt
10.1038/nature12373
10.1126/science.aax0758
# 10.xxxx/commented-out
```

```python
result = crl.check_doi_list("dois.txt")
```

## Metadata Validation

When `validate_metadata=True`, each found DOI is checked for:

| Check | Issue reported |
|-------|---------------|
| Missing abstract | "Missing abstract in database" |
| Missing authors | "Missing author list" |
| Missing year | "Missing publication year" |

## CLI Usage

```bash
crossref-local check bibliography.bib
crossref-local check dois.txt
crossref-local check -d 10.1038/nature12373 -d 10.1126/science.aax0758
crossref-local check bibliography.bib --json
crossref-local check bibliography.bib --save report.json
```
