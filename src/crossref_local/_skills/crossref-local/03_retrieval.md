---
package: crossref-local
skill: retrieval
---

# Retrieval

Fetch full metadata for one or many DOIs, and enrich search results with
citation counts and reference lists.

## Signatures

```python
get(doi: str) -> Work | None

get_many(dois: list[str]) -> list[Work]

enrich(
    results: SearchResult,
    include_citations: bool = True,
    include_references: bool = True,
) -> SearchResult

enrich_dois(
    dois: list[str],
    include_citations: bool = True,
    include_references: bool = True,
) -> list[Work]
```

## `get()` — Single DOI Lookup

Returns `None` if not found; never raises for missing DOIs.

```python
import crossref_local as crl

work = crl.get("10.1038/nature12373")
if work:
    print(work.title)
    print(work.citation_count)
    print(work.to_bibtex())
```

## `get_many()` — Batch Lookup

Missing DOIs are silently skipped (no exception).

```python
dois = ["10.1038/nature12373", "10.1126/science.aax0758", "10.xxxx/invalid"]
works = crl.get_many(dois)
# Returns 2 Work objects; invalid DOI is skipped
```

## `enrich()` — Enrich SearchResult

`search()` returns lightweight metadata for speed. `enrich()` fetches full
metadata for each work in the result, adding `citation_count` and `references`.

```python
results = crl.search("machine learning", limit=10)
enriched = crl.enrich(results)
for work in enriched:
    print(f"{work.title}: {work.citation_count} citations, "
          f"{len(work.references)} references")
```

## `enrich_dois()` — Enrich DOI List

Convenience wrapper around `get_many()` for a list of DOIs.

```python
dois = ["10.1038/nature12373", "10.1126/science.aax0758"]
works = crl.enrich_dois(dois)
for w in works:
    print(f"{w.doi}: {w.citation_count} citations, {len(w.references)} refs")
```

## Typical Workflow

```python
# 1. Search for papers (fast, basic metadata)
results = crl.search("hippocampal replay", limit=20)

# 2. Get DOIs of most relevant papers
doi_list = [w.doi for w in results[:5]]

# 3. Enrich with full metadata
works = crl.enrich_dois(doi_list)

# 4. Save as BibTeX
crl.save(works, "papers.bib", format="bibtex")
```

## Notes

- `search()` is faster than `get()` for initial discovery
- `enrich()` makes N database calls (one per work) — use `get_many()` for batch
- Both `enrich()` and `enrich_dois()` are decorated with `@supports_return_as`
