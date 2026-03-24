# CLI Commands

```bash
# Search
crossref-local search "deep learning EEG" -n 20
crossref-local search "CRISPR" -n 5 -a --json      # With abstracts, JSON output
crossref-local search-by-doi 10.1038/nature12373

# Check citations
crossref-local check bibliography.bib
crossref-local check dois.txt --json

# Status
crossref-local status
crossref-local status --json

# Server
crossref-local relay --dry-run            # Preview server config
crossref-local relay --port 8080          # Start HTTP relay

# MCP server
crossref-local mcp start                  # stdio (Claude Desktop)
crossref-local mcp start -t http          # HTTP transport
crossref-local mcp doctor                 # Diagnose setup
crossref-local mcp list-tools -vv         # List tools with descriptions

# Browse API
crossref-local list-python-apis -v        # List all public APIs

# Documentation & Skills
crossref-local docs list
crossref-local docs get quickstart
crossref-local skills list
crossref-local skills get
```
