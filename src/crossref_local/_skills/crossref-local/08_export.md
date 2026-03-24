---
package: crossref-local
skill: export
---

# Export

Save `Work`, `SearchResult`, or lists of `Work` objects to files.

## Signature

```python
save(
    data: Work | SearchResult | list[Work],
    path: str | Path,
    format: str = "json",
    include_abstract: bool = True,
) -> str   # returns path to saved file
```

## Supported Formats

| Format | Extension | Content |
|--------|-----------|---------|
| `json` | `.json` | JSON with all fields; includes query/total/elapsed metadata for SearchResult |
| `bibtex` | `.bib` | BibTeX entries; type mapped from CrossRef type |
| `text` | `.txt` | Human-readable; one work per block with optional abstracts |

`SUPPORTED_FORMATS = ["text", "json", "bibtex"]`

## Examples

```python
import crossref_local as crl

results = crl.search("hippocampal replay", limit=20)

# Save SearchResult
crl.save(results, "results.json")
crl.save(results, "results.bib", format="bibtex")
crl.save(results, "results.txt", format="text", include_abstract=False)

# Save single Work
work = crl.get("10.1038/nature12373")
crl.save(work, "paper.json")
crl.save(work, "paper.bib", format="bibtex")

# Save list of Works
works = crl.get_many(["10.1038/nature12373", "10.1126/science.aax0758"])
crl.save(works, "papers.json")

# Via methods on objects
results.save("results.json")
results.save("results.bib", format="bibtex")
work.save("paper.bib", format="bibtex")
```

## BibTeX Type Mapping

| CrossRef type | BibTeX type |
|--------------|-------------|
| `journal-article` | `@article` |
| `book-chapter` | `@incollection` |
| `book` | `@book` |
| `proceedings-article` | `@inproceedings` |
| `dissertation` | `@phdthesis` |
| `report` | `@techreport` |
| (other) | `@misc` |

BibTeX keys are generated from DOIs by replacing `/`, `.`, `-` with `_`.

## JSON Structure

For a `SearchResult`:

```json
{
  "query": "hippocampal replay",
  "total": 42315,
  "elapsed_ms": 18.4,
  "works": [
    {
      "doi": "10.1038/...",
      "title": "...",
      "authors": ["A. Author", "B. Author"],
      "year": 2021,
      "journal": "Nature",
      "issn": "0028-0836",
      "volume": "591",
      "issue": "7849",
      "page": "333-340",
      "publisher": "Springer Nature",
      "type": "journal-article",
      "abstract": "...",
      "url": "http://dx.doi.org/...",
      "citation_count": 412,
      "references": ["10.1038/...", ...],
      "impact_factor": null,
      "impact_factor_source": null
    }
  ]
}
```

## Text Format

```
Search: hippocampal replay
Found: 42,315 matches
Time: 18.4ms

============================================================

[1]
Hippocampal Replay (2021)
Authors: A. Author, B. Author
Journal: Nature, 591(7849), 333-340
DOI: 10.1038/...
Citations: 412

----------------------------------------
```
