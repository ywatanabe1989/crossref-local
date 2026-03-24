---
package: crossref-local
skill: cli
---

# Command-Line Interface

Entry point: `crossref-local` (installs from `crossref_local.cli:main`)

## Global Options

```
crossref-local [--http] [--api-url URL] [--help-recursive] COMMAND
```

| Option | Description |
|--------|-------------|
| `--http` | Force HTTP mode (connect to relay server) |
| `--api-url URL` | API URL; also via `CROSSREF_LOCAL_API_URL` |
| `--help-recursive` | Print help for all subcommands |
| `--version` | Show version |

## Commands

### `search`

```
crossref-local search QUERY [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `-n N`, `--number N` | Number of results (default: 10) |
| `-o N`, `--offset N` | Skip first N results |
| `-a`, `--abstracts` | Show abstracts |
| `-A`, `--authors` | Show author list |
| `-if`, `--impact-factor` | Show OpenAlex impact factor |
| `--json` | Output as JSON |
| `--save FILE` | Save results to file |
| `--format {text,json,bibtex}` | Format for `--save` (default: json) |

```bash
crossref-local search "hippocampal sharp wave ripples"
crossref-local search "CRISPR" -n 20 -a -A --json
crossref-local search "machine learning" --save papers.bib --format bibtex
crossref-local search "epilepsy" -n 100 --save results.json
```

### `search-by-doi`

```
crossref-local search-by-doi DOI [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--json` | Output as JSON |
| `--citation` | Output formatted APA citation |
| `--save FILE` | Save to file |
| `--format {text,json,bibtex}` | Format for `--save` (default: json) |

```bash
crossref-local search-by-doi 10.1038/nature12373
crossref-local search-by-doi 10.1038/nature12373 --citation
crossref-local search-by-doi 10.1038/nature12373 --json
crossref-local search-by-doi 10.1038/nature12373 --save paper.bib --format bibtex
```

### `check`

```
crossref-local check [FILE] [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `FILE` | BibTeX file (.bib) or DOI list file |
| `-d DOI` | Check specific DOI (repeatable) |
| `-f {bibtex,doi-list,auto}` | Input format (default: auto-detect) |
| `--no-validate` | Skip metadata validation |
| `--no-suggest` | Skip enrichment suggestions |
| `--json` | Output as JSON |
| `--save FILE` | Save results to file |
| `--save-format {json,text}` | Format for `--save` |

```bash
crossref-local check bibliography.bib
crossref-local check dois.txt
crossref-local check -d 10.1038/nature12373 -d 10.1126/science.aax0758
crossref-local check bibliography.bib --json
crossref-local check bibliography.bib --save report.json
# From stdin
echo "10.1038/nature12373" | crossref-local check
```

### `status`

```
crossref-local status [--json]
```

Shows environment variables, database locations, API health, and counts.

### `relay`

Run an HTTP relay server exposing the SQLite DB over REST.

```
crossref-local relay [OPTIONS]
```

| Option | Description |
|--------|-------------|
| `--host HOST` | Bind host (default: 0.0.0.0, env: `CROSSREF_LOCAL_HOST`) |
| `--port PORT` | Port (default: 31291, env: `CROSSREF_LOCAL_PORT`) |
| `--force` | Kill existing process using the port |
| `--dry-run` | Show what would be started |

```bash
crossref-local relay
crossref-local relay --port 8080
crossref-local relay --force
```

Requires: `pip install fastapi uvicorn`

### `mcp`

MCP server subcommands. See [11_mcp.md](11_mcp.md).

```bash
crossref-local mcp start              # stdio (Claude Desktop)
crossref-local mcp start -t http      # HTTP transport
crossref-local mcp doctor             # diagnose setup
crossref-local mcp installation       # show client config
crossref-local mcp list-tools         # list MCP tools
crossref-local mcp list-tools -vvv    # with full docs
```

### `list-python-apis`

```
crossref-local list-python-apis [-v|-vv|-vvv] [-d DEPTH] [--json]
```

Lists Python API signatures (delegates to `scitex introspect api`).
