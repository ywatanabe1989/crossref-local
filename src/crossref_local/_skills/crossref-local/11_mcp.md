---
package: crossref-local
skill: mcp
---

# MCP Server

Exposes crossref-local as Model Context Protocol tools for Claude Desktop,
Claude Code, and other MCP clients.

Entry points:
- `crossref-local mcp start` (via CLI)
- `crossref-local-mcp` (direct entry point, stdio)

Requires: `pip install crossref-local[mcp]` (installs `fastmcp`)

## MCP Tools Reference

### `search`

```
search(
    query: str,
    limit: int = 10,
    offset: int = 0,
    with_abstracts: bool = False,
    save_path: str | None = None,
    save_format: str = "json",         # "text", "json", "bibtex"
) -> str   # JSON
```

Full-text search. Returns `{query, total, returned, elapsed_ms, works[]}`.
Each work: `{doi, title, authors, year, journal}` (+ `abstract` if requested).

### `search_by_doi`

```
search_by_doi(
    doi: str,
    as_citation: bool = False,
    save_path: str | None = None,
    save_format: str = "json",
) -> str   # JSON or APA citation string
```

Full metadata for a single DOI. Returns `Work.to_dict()` as JSON, or APA
citation string if `as_citation=True`.

### `status`

```
status() -> str   # JSON
```

Returns `{mode, status, db_path, works, fts_indexed, citations}`.

### `enrich_dois`

```
enrich_dois(dois: list[str]) -> str   # JSON
```

Fetch full metadata for a list of DOIs.
Returns `{requested, found, works[]}` with complete Work dicts.

### `check_citations`

```
check_citations(
    identifiers: list[str],
    validate_metadata: bool = True,
    suggest_enrichment: bool = True,
) -> str   # JSON
```

Validate DOIs. Returns `{summary: {total, found, missing, with_issues}, entries[]}`.

### `check_bibtex_file`

```
check_bibtex_file(
    file_path: str,               # absolute path
    validate_metadata: bool = True,
    suggest_enrichment: bool = True,
) -> str   # JSON
```

### Cache Tools

| Tool | Signature summary |
|------|-------------------|
| `cache_create` | `(name, query, limit=1000) -> JSON` |
| `cache_query` | `(name, fields=None, include_abstract=False, ..., year_min, year_max, journal, limit) -> JSON` |
| `cache_stats` | `(name) -> JSON` |
| `cache_list` | `() -> JSON` |
| `cache_top_cited` | `(name, n=20, year_min=None, year_max=None) -> JSON` |
| `cache_citation_summary` | `(name) -> JSON` |
| `cache_plot_scatter` | `(name, output, top_n=10) -> JSON` |
| `cache_plot_network` | `(name, output, max_nodes=100) -> JSON` |
| `cache_export` | `(name, output_path, format="json", fields=None) -> JSON` |

## Transport Options

| Transport | Use case | Command |
|-----------|----------|---------|
| `stdio` | Claude Desktop / Claude Code local | `crossref-local mcp start` |
| `http` | Remote server, persistent | `crossref-local mcp start -t http --host 0.0.0.0 --port 8082` |
| `sse` | (deprecated as of MCP spec 2025-03-26) | `crossref-local mcp start -t sse` |

## Client Configuration

### Local (stdio) — Claude Desktop / Claude Code

```json
{
  "mcpServers": {
    "crossref-local": {
      "command": "crossref-local",
      "args": ["mcp", "start"],
      "env": {
        "CROSSREF_LOCAL_DB": "/path/to/crossref.db"
      }
    }
  }
}
```

### Remote (HTTP)

Server side:
```bash
crossref-local mcp start -t http --host 0.0.0.0 --port 8082
```

Client config:
```json
{
  "mcpServers": {
    "crossref-remote": {
      "url": "http://your-server:8082/mcp"
    }
  }
}
```

## Diagnostics

```bash
crossref-local mcp doctor         # checks fastmcp install + DB access
crossref-local mcp installation   # prints client config templates
crossref-local mcp list-tools     # all tool names
crossref-local mcp list-tools -v  # with signatures
crossref-local mcp list-tools -vv # with signatures + descriptions
```

## Typical MCP Workflow

```
1. search("epilepsy seizure prediction", limit=20)
   -> get DOIs and basic metadata

2. enrich_dois([doi1, doi2, ...])
   -> get citation_count, references, full metadata

3. cache_create("epilepsy", "epilepsy seizure prediction", limit=500)
   -> build persistent topic cache

4. cache_query("epilepsy", year_min=2020, include_citations=True, limit=50)
   -> filtered results for analysis

5. cache_plot_scatter("epilepsy", "scatter.png")
   -> year vs citations visualization
```
