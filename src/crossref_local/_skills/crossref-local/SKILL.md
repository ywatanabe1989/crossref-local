---
name: crossref-local
description: |
  [WHAT] Offline, zero-API-key DOI lookup + full-text search over the CrossRef corpus.
  [WHEN] Use when the user asks to "look up a DOI", "resolve DOI to BibTeX", "find a paper by DOI", "enrich BibTeX with missing fields".
  [HOW] `import crossref_local` then call `habanero.Crossref()`.
tags: [crossref-local]
allowed-tools: mcp__scitex__crossref_*
primary_interface: python
interfaces:
  python: 3
  cli: 2
  mcp: 2
  skills: 2
  hook: 0
  http: 0
---


# crossref-local

> **Interfaces:** Python ⭐⭐⭐ (primary) · CLI ⭐⭐ · MCP ⭐⭐ · Skills ⭐⭐ · Hook — · HTTP —

Local mirror of the CrossRef database with FTS5 full-text search across
167M+ scholarly works — offline, millisecond queries, no rate limits. Also
exposes citation networks, per-topic caches, and an HTTP/MCP relay.

## Installation & import

`pip install crossref-local` installs the standalone:

```python
import crossref_local
```

This package does not ship as a submodule of the `scitex` umbrella.

## Core concepts

- [01_configuration.md](01_configuration.md) — env vars, DB vs HTTP mode, relay server
- [02_search.md](02_search.md) — `search()`, `count()`, `exists()`, FTS5 syntax
- [03_retrieval.md](03_retrieval.md) — `get()`, `get_many()`, `enrich()`, `enrich_dois()`
- [04_models.md](04_models.md) — `Work`, `SearchResult` dataclasses
- [05_citations.md](05_citations.md) — `get_citing()`, `get_cited()`, `CitationNetwork`
- [06_checker.md](06_checker.md) — `check_citations()`, `check_bibtex()`, `check_doi_list()`
- [07_cache.md](07_cache.md) — topic caches: create, query, stats, plots, export
- [08_export.md](08_export.md) — `save()` with json / bibtex / text formats
- [09_async.md](09_async.md) — `aio.search()`, `aio.count_many()`

## Interfaces

- [10_cli.md](10_cli.md) — `crossref-local` CLI (search, check, relay, mcp)
- [11_mcp.md](11_mcp.md) — MCP server, tools reference, client config


## Environment

- [12_env-vars.md](12_env-vars.md) — SCITEX_* env vars read by crossref-local at runtime
