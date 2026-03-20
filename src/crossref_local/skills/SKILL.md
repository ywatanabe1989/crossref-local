---
name: crossref-local
description: Local CrossRef database with 167M+ works and full-text search. Use when resolving DOIs, searching publications, enriching bibliographies, checking citations, or calculating impact factors.
allowed-tools: mcp__scitex__crossref_*
---

# Local CrossRef with crossref-local

## Quick Start

```python
from crossref_local import search, get, count

# Full-text search (22ms for 541 matches across 167M records)
results = search("hippocampal sharp wave ripples")
for work in results:
    print(f"{work.title} ({work.year})")

# Get by DOI
work = get("10.1126/science.aax0758")
print(work.citation())

# Count matches
n = count("machine learning")  # 477,922 matches
```

## Common Workflows

### "I need to find papers on a topic"

```python
from crossref_local import search

results = search("CRISPR genome editing", limit=20)
for work in results:
    print(f"{work.title} ({work.year}) - {work.doi}")
```

### "I have DOIs and need metadata"

```python
from crossref_local import get, get_many, enrich_dois

# Single DOI
work = get("10.1038/nature12373")

# Multiple DOIs
works = get_many(["10.1038/nature12373", "10.1126/science.aax0758"])

# Enrich with citation counts and references
enriched = enrich_dois(["10.1038/nature12373"])
```

### "I need citation information"

```python
from crossref_local import get_citing, get_cited, get_citation_count

citing = get_citing("10.1038/nature12373")   # Papers citing this work
cited = get_cited("10.1038/nature12373")     # Papers this work cites
count = get_citation_count("10.1038/nature12373")  # 1539
```

### "I want to validate my bibliography"

```python
from crossref_local import check_bibtex, check_citations

# Check a BibTeX file
report = check_bibtex("references.bib")

# Check DOIs in a list
report = check_doi_list("dois.txt")
```

### "I need a citation network visualization"

```python
from crossref_local import CitationNetwork

network = CitationNetwork("10.1038/nature12373", depth=2)
network.save_html("citation_network.html")  # requires: pip install crossref-local[viz]
```

### "I want to calculate impact factors"

```python
from crossref_local.impact_factor import ImpactFactorCalculator

with ImpactFactorCalculator() as calc:
    result = calc.calculate_impact_factor("Nature", target_year=2023)
    print(f"IF: {result['impact_factor']:.3f}")  # 54.067
```

### "I need async operations"

```python
from crossref_local import aio

async def main():
    counts = await aio.count_many(["CRISPR", "neural network", "climate"])
    results = await aio.search("machine learning")
```

## Output Formats

Every search returns `Work` objects with consistent attributes:

```python
work = get("10.1038/nature12373")
# Attributes: doi, title, year, authors, journal, abstract,
#             citation_count, references, type, member
work.citation()  # Formatted citation string
```

## CLI Commands

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

## MCP Tools (for AI agents)

| Tool | Purpose |
|------|---------|
| `crossref_search` | Full-text search across 167M+ works |
| `crossref_search_by_doi` | Get work by DOI |
| `crossref_enrich_dois` | Enrich DOIs with citation counts and references |
| `crossref_check_bibtex_file` | Validate BibTeX file against database |
| `crossref_check_citations` | Check citation accuracy |
| `crossref_status` | Database statistics and configuration |
| `crossref_cache_create` | Create search cache/project |
| `crossref_cache_query` | Query within cache |
| `crossref_cache_export` | Export cache results (BibTeX, JSON, CSV) |
| `crossref_cache_list` | List caches |
| `crossref_cache_stats` | Cache statistics |
| `crossref_cache_top_cited` | Top cited papers in cache |
| `crossref_cache_citation_summary` | Citation summary for cache |
| `crossref_cache_plot_scatter` | Plot citation scatter diagram |
| `crossref_cache_plot_network` | Plot citation network graph |

## Performance Reference

| Query | Matches | Time |
|-------|---------|------|
| `hippocampal sharp wave ripples` | 541 | 22ms |
| `machine learning` | 477,922 | 113ms |
| `CRISPR genome editing` | 12,170 | 257ms |

Searching 167M records in milliseconds via FTS5.
