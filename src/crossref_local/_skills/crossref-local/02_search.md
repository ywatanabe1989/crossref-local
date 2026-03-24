---
package: crossref-local
skill: search
---

# Search

Full-text search across titles, abstracts, and authors using SQLite FTS5 index.

## Signatures

```python
search(
    query: str,
    limit: int = 10,
    offset: int = 0,
    with_if: bool = False,
) -> SearchResult

count(query: str) -> int

exists(doi: str) -> bool
```

## Parameters

### `search()`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | required | FTS5 search query |
| `limit` | int | 10 | Max results to return |
| `offset` | int | 0 | Skip first N results (pagination) |
| `with_if` | bool | False | Include OpenAlex impact factor data |

### `count()`

Returns total number of matching works without fetching results. Efficient for
pagination planning.

### `exists()`

Returns `True` if the DOI is present in the database.

## FTS5 Query Syntax

| Syntax | Meaning | Example |
|--------|---------|---------|
| `word` | Match word | `CRISPR` |
| `"exact phrase"` | Exact phrase | `"sharp wave ripples"` |
| `word1 AND word2` | Both required | `neural AND network` |
| `word1 OR word2` | Either | `hippocampus OR cortex` |
| `word1 NOT word2` | Exclude | `seizure NOT epilepsy` |
| `word*` | Prefix match | `neuro*` |

## Examples

```python
import crossref_local as crl

# Basic search
results = crl.search("hippocampal sharp wave ripples")
print(f"Found {results.total:,} matches in {results.elapsed_ms:.1f}ms")
for work in results:
    print(f"  {work.title} ({work.year}) DOI:{work.doi}")

# Paginate
page1 = crl.search("machine learning", limit=20, offset=0)
page2 = crl.search("machine learning", limit=20, offset=20)

# Count only
n = crl.count("CRISPR AND cancer")
print(f"{n:,} papers on CRISPR and cancer")

# Check existence
if crl.exists("10.1038/nature12373"):
    print("DOI is in database")

# FTS5 operators
results = crl.search('"deep learning" AND brain NOT review', limit=50)

# With impact factor
results = crl.search("epilepsy seizure prediction", with_if=True)
for work in results:
    if work.impact_factor:
        print(f"IF {work.impact_factor:.1f}: {work.title}")
```

## `@supports_return_as` Decorator

All search functions are decorated with `@supports_return_as` from
`scitex_dev`, enabling alternate return formats:

```python
# Return as pandas DataFrame
df = crl.search("CRISPR", limit=100, return_as="dataframe")

# Return as JSON string
json_str = crl.count("deep learning", return_as="json")
```

## Performance Notes

- FTS5 index covers titles, abstracts, and authors
- Typical search latency: 5–50ms for common queries
- `count()` is slightly faster than `search()` for existence checks
- `exists()` uses a direct indexed lookup — fastest for single DOI checks
