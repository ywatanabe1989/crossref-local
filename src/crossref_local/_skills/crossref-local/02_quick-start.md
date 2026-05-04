---
description: |
  [TOPIC] Quick start
  [DETAILS] Smallest example — search by title, get by DOI, enrich a BibTeX file.
tags: [crossref-local-quick-start]
---

# Quick Start

## Python — search

```python
import crossref_local as crl

results = crl.search("CRISPR base editing", limit=10)
for w in results.works:
    print(w.doi, w.title[:80])
```

## Python — get + enrich

```python
work = crl.get("10.1126/science.aax0758")
print(work.title, work.year, work.authors)

# Enrich a BibTeX file with abstracts/DOIs/IF
crl.enrich("refs.bib", out="refs-enriched.bib")
```

## Python — async

```python
from crossref_local import aio
results = await aio.search("graph neural network")
```

## CLI

```bash
crossref-local search "machine learning" -n 5
crossref-local search-by-doi 10.1038/nature12373
crossref-local check-citations bibliography.bib
crossref-local show-status
```

## HTTP relay (multi-process / multi-host)

```bash
# host A
crossref-local relay --port 31291

# host B
crossref-local --http --api-url http://A:31291 search "CRISPR"
```

## Next

- [03_python-api.md](03_python-api.md) — full surface
- [04_cli-reference.md](04_cli-reference.md) — all CLI commands
- [13_configuration.md](13_configuration.md) — modes + env vars
- [16_models.md](16_models.md) — `Work`, `SearchResult` dataclasses
