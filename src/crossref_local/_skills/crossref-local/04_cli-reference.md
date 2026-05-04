---
description: |
  [TOPIC] CLI reference
  [DETAILS] `crossref-local` and `crossref-local-mcp` console entries — search, search-by-doi, check-citations, show-status, mcp, relay, docs, list-python-apis.
tags: [crossref-local-cli-reference]
---

# CLI Reference

```
crossref-local [OPTIONS] COMMAND [ARGS]...
```

Local CrossRef database with 167M+ works and full-text search.
Two console entries are shipped: `crossref-local` (main) and
`crossref-local-mcp` (MCP server convenience).

## Global options

| Flag | Purpose |
|---|---|
| `-h`, `--help` | Show this message and exit |
| `--version` / `-V` | Show / show-version (alias) |
| `--http` | Use HTTP API instead of direct database |
| `--api-url TEXT` | API URL for http mode (default: auto-detect) |
| `--json` | Emit machine-readable JSON (propagated to subcommands) |
| `--help-recursive` | Show help for all commands recursively |

## Configuration precedence

```
./config.yaml -> $CROSSREF_LOCAL_CONFIG -> ~/.scitex/crossref-local/config.yaml -> defaults
```

## Commands by category

### Lookup

| Command | Purpose |
|---|---|
| `search` | Search for works by title, abstract, or authors |
| `search-by-doi` | Search for a work by DOI |

### Citation management

| Command | Purpose |
|---|---|
| `check-citations` (alias `check`) | Check citations against the local CrossRef DB; accepts BibTeX, DOI list, or `-d DOI` |

### Status + introspection

| Command | Purpose |
|---|---|
| `show-status` (alias `status`) | Show status and configuration (DB path, mode, version) |
| `list-python-apis` | List Python APIs (alias for `scitex introspect api crossref_local`) |

### Servers

| Command | Purpose |
|---|---|
| `relay` | Run HTTP relay server (FastAPI) for remote DB access |
| `mcp start` | Start the MCP server |
| `mcp doctor` | Diagnose MCP setup |
| `mcp list-tools` | List available MCP tools |
| `mcp show-installation` | Print MCP client installation instructions |

### Docs

| Command | Purpose |
|---|---|
| `docs list` | List doc pages |
| `docs get [PAGE]` | Show specific doc page |
| `skills` | View package skills (workflow-oriented guides) |

## Common flags

`search`:
```
-n, --number INTEGER         Number of results (default 10)
-o, --offset INTEGER         Skip first N results
-a, --abstracts              Show abstracts
-A, --authors                Show authors
-if, --impact-factor         Show journal impact factor
--save PATH --format FMT     Save to file (text|json|bibtex)
```

`search-by-doi`:
```
--citation                   Output as citation
--save PATH --format FMT     Save to file (text|json|bibtex)
```

`check-citations`:
```
-d, --doi TEXT                  Check specific DOI(s)
-f, --format [bibtex|doi-list|auto]   Input format
--no-validate / --no-suggest    Skip validation / enrichment hints
--save PATH --save-format FMT   Save report
```

`relay`:
```
--host TEXT       Host to bind
--port INTEGER    Port (default 31291)
--force           Kill existing process if port in use
--dry-run         Show what would start without starting
```

## Examples

```bash
crossref-local search "CRISPR base editing" -n 5 -A -if
crossref-local search-by-doi 10.1126/science.aax0758 --citation
crossref-local check-citations bibliography.bib --json --save report.json
crossref-local relay --port 31291
crossref-local --http --api-url http://hostA:31291 search "neural network"
crossref-local mcp doctor
```

## See also

- [10_cli.md](10_cli.md) — extended legacy CLI notes
- [11_mcp.md](11_mcp.md) — MCP tool catalog
- [13_configuration.md](13_configuration.md) — modes + env vars
