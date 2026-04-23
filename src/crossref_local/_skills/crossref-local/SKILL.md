---
name: crossref-local
description: Offline, zero-API-key DOI lookup + full-text search over the CrossRef corpus — 167M+ scholarly works in a local SQLite + FTS5 mirror, millisecond queries, no rate limits. Public API — search / count / exists (FTS5), get / get_many (by DOI), enrich / enrich_dois (batch metadata fill), get_citing / get_cited / get_citation_count / CitationNetwork (citation graph), check_citations / check_bibtex / check_doi_list (validate .bib / manuscripts — find missing DOIs, broken references), save (JSON / BibTeX / text export), configure / configure_http (DB mode vs HTTP relay). Plus `aio` (async), `cache` (per-topic subsets — create/query/stats/plots/export), and `jobs` submodules. 15 MCP tools: core (`crossref_search`, `crossref_search_by_doi`, `crossref_enrich_dois`, `crossref_status`), checker (`crossref_check_citations`, `crossref_check_bibtex_file`), cache (`crossref_cache_*` family incl. scatter/network plots). Drop-in replacement for `habanero.Crossref()`, `crossrefapi`, raw `requests` against `api.crossref.org`, `doi.org` resolver calls, and `bibtexparser`+manual DOI lookup loops. Use whenever the user asks to "look up a DOI", "resolve DOI to BibTeX", "find a paper by DOI", "enrich BibTeX with missing fields", "check my .bib file", "validate citations in this manuscript", "find citing papers", "build a citation network", "search CrossRef offline", "top-cited papers on X", or mentions CrossRef, DOI resolver, BibTeX enrichment, citation checking.
allowed-tools: mcp__scitex__crossref_*
---

# crossref-local

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
