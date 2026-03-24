---
package: crossref-local
version: 0.6.4
description: Local CrossRef database with 167M+ works and full-text search
---

# crossref-local Skills Index

Local mirror of the CrossRef database. Full-text search across 167M+ scholarly
works, citation network analysis, and paper cache management — all offline, no
rate limits.

## Sub-skill Files

| File | Topic |
|------|-------|
| [crossref-local/01_configuration.md](crossref-local/01_configuration.md) | Setup, env vars, DB vs HTTP mode |
| [crossref-local/02_search.md](crossref-local/02_search.md) | `search()`, `count()`, `exists()`, FTS5 syntax |
| [crossref-local/03_retrieval.md](crossref-local/03_retrieval.md) | `get()`, `get_many()`, `enrich()`, `enrich_dois()` |
| [crossref-local/04_models.md](crossref-local/04_models.md) | `Work`, `SearchResult` dataclasses and methods |
| [crossref-local/05_citations.md](crossref-local/05_citations.md) | `get_citing()`, `get_cited()`, `CitationNetwork` |
| [crossref-local/06_checker.md](crossref-local/06_checker.md) | `check_citations()`, `check_bibtex()`, `check_doi_list()` |
| [crossref-local/07_cache.md](crossref-local/07_cache.md) | `cache.create()`, `cache.query()`, `cache.stats()` |
| [crossref-local/08_export.md](crossref-local/08_export.md) | `save()`, formats: json/bibtex/text |
| [crossref-local/09_async.md](crossref-local/09_async.md) | `aio.search()`, `aio.count_many()` |
| [crossref-local/10_cli.md](crossref-local/10_cli.md) | CLI commands: search, check, relay, mcp |
| [crossref-local/11_mcp.md](crossref-local/11_mcp.md) | MCP server tools and client config |

## MCP Tools

| Tool | Description |
|------|-------------|
| `search` | FTS5 full-text search across 167M+ papers |
| `search_by_doi` | Lookup by DOI, returns full metadata |
| `status` | Database stats (works, FTS indexed, citations) |
| `enrich_dois` | Fetch full metadata for a list of DOIs |
| `check_citations` | Validate DOI list against database |
| `check_bibtex_file` | Validate all DOIs in a .bib file |
| `cache_create` | Build topic cache from search query |
| `cache_query` | Filter/project cached papers |
| `cache_stats` | Year distribution, top journals, citation stats |
| `cache_list` | List all caches |
| `cache_top_cited` | Top cited papers from cache |
| `cache_citation_summary` | Citation statistics for cache |
| `cache_plot_scatter` | Year vs citations scatter plot |
| `cache_plot_network` | Interactive citation network HTML |
| `cache_export` | Export cache to json/csv/bibtex/dois |

## CLI Summary

```
crossref-local search QUERY [-n N] [-a] [-A] [-if] [--json] [--save FILE]
crossref-local search-by-doi DOI [--json] [--citation] [--save FILE]
crossref-local check [FILE] [-d DOI] [--json] [--save FILE]
crossref-local status [--json]
crossref-local relay [--port PORT] [--force]
crossref-local mcp start [-t stdio|http|sse] [--host HOST] [--port PORT]
crossref-local mcp doctor
crossref-local mcp installation
crossref-local mcp list-tools [-v|-vv|-vvv]
```

## Quick Start

```python
import crossref_local as crl

# Configure (or set CROSSREF_LOCAL_DB env var)
crl.configure("/path/to/crossref.db")

# Search
results = crl.search("hippocampal sharp wave ripples", limit=10)

# Retrieve by DOI
work = crl.get("10.1126/science.aax0758")

# Check citations
result = crl.check_bibtex("bibliography.bib")
```
