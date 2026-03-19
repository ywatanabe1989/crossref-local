---
name: crossref-local
description: Local CrossRef database with 167M+ works and full-text search. Use when resolving DOIs, searching publications, enriching bibliographies, or checking citations.
allowed-tools: mcp__scitex__crossref_*
---

# Local CrossRef with crossref-local

## Quick Start

```python
from crossref_local import search, search_by_doi

# Search works
results = search("machine learning neuroscience", limit=20)

# Get by DOI
work = search_by_doi("10.1038/s41586-024-00001-1")

# Enrich DOIs
enriched = enrich_dois(["10.1038/s41586-024-00001-1"])
```

## CLI Commands

```bash
crossref-local search "deep learning EEG" --limit 20
crossref-local search-by-doi 10.1038/s41586-024-00001-1
crossref-local enrich-dois 10.1038/s41586-024-00001-1
crossref-local check-bibtex refs.bib
crossref-local status

# Cache management
crossref-local cache create --name my-review
crossref-local cache query my-review "neural oscillations"
crossref-local cache export my-review -o results.bib

# Skills
crossref-local skills list
```

## MCP Tools

| Tool | Purpose |
|------|---------|
| `crossref_search` | Full-text search across 167M+ works |
| `crossref_search_by_doi` | Get work by DOI |
| `crossref_enrich_dois` | Enrich DOIs with metadata |
| `crossref_check_bibtex_file` | Validate BibTeX file |
| `crossref_check_citations` | Check citation accuracy |
| `crossref_status` | Database status |
| `crossref_cache_create` | Create search cache/project |
| `crossref_cache_query` | Query within cache |
| `crossref_cache_export` | Export cache results |
| `crossref_cache_list` | List caches |
| `crossref_cache_stats` | Cache statistics |
| `crossref_cache_top_cited` | Top cited in cache |
| `crossref_cache_citation_summary` | Citation summary |
| `crossref_cache_plot_scatter` | Plot citation scatter |
| `crossref_cache_plot_network` | Plot citation network |
