# CrossRef Local

Local CrossRef database with 167M+ scholarly works, full-text search, and impact factor calculation.

[![Tests](https://github.com/ywatanabe1989/crossref-local/actions/workflows/test.yml/badge.svg)](https://github.com/ywatanabe1989/crossref-local/actions/workflows/test.yml)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](LICENSE)

<p align="center">
  <img src="examples/readme_figure.png" alt="CrossRef Local Demo" width="800"/>
</p>

<details>
<summary><strong>Why CrossRef Local?</strong></summary>

**Built for the LLM era** - features that matter for AI research assistants:

| Feature | Benefit |
|---------|---------|
| 📝 **Abstracts** | Full text for semantic understanding |
| 📊 **Impact Factor** | Filter by journal quality |
| 🔗 **Citations** | Prioritize influential papers |
| ⚡ **Speed** | 167M records in ms, no rate limits |

Perfect for: RAG systems, research assistants, literature review automation.

</details>

<details>
<summary><strong>Installation</strong></summary>

```bash
pip install crossref-local
```

From source:
```bash
git clone https://github.com/ywatanabe1989/crossref-local
cd crossref-local && make install
```

Database setup (1.5 TB, ~2 weeks to build):
```bash
# 1. Download CrossRef data (~100GB compressed)
aria2c "https://academictorrents.com/details/..."

# 2. Build SQLite database (~days)
pip install dois2sqlite
dois2sqlite build /path/to/crossref-data ./data/crossref.db

# 3. Build FTS5 index (~60 hours) & citations table (~days)
make fts-build-screen
make citations-build-screen
```

</details>

<details>
<summary><strong>Python API</strong></summary>

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

Async API:
```python
from crossref_local import aio

async def main():
    counts = await aio.count_many(["CRISPR", "neural network", "climate"])
    results = await aio.search("machine learning")
```

</details>

<details>
<summary><strong>CLI</strong></summary>

```bash
crossref-local search "CRISPR genome editing" -n 5
crossref-local get 10.1038/nature12373
crossref-local impact-factor Nature -y 2023  # IF: 54.067
crossref-local info  # Database stats
```

With abstracts (`-a` flag):
```
$ crossref-local search "RS-1 enhances CRISPR" -n 1 -a

Found 4 matches in 128.4ms

1. RS-1 enhances CRISPR/Cas9- and TALEN-mediated knock-in efficiency (2016)
   DOI: 10.1038/ncomms10548
   Journal: Nature Communications
   Abstract: Zinc-finger nuclease, transcription activator-like effector nuclease
   and CRISPR/Cas9 are becoming major tools for genome editing...
```

</details>

<details>
<summary><strong>HTTP API</strong></summary>

Start the FastAPI server:
```bash
crossref-local api --host 0.0.0.0 --port 3333
```

Endpoints:
```bash
# Search works (FTS5)
curl "http://localhost:3333/works?q=CRISPR&limit=10"

# Get by DOI
curl "http://localhost:3333/works/10.1038/nature12373"

# Batch DOI lookup
curl -X POST "http://localhost:3333/works/batch" \
  -H "Content-Type: application/json" \
  -d '{"dois": ["10.1038/nature12373", "10.1126/science.aax0758"]}'

# Database info
curl "http://localhost:3333/info"
```

Remote access via SSH tunnel:
```bash
# On local machine
ssh -L 3333:127.0.0.1:3333 nas

# Python client
from crossref_local import configure_remote
configure_remote("http://localhost:3333")
```

</details>

<details>
<summary><strong>MCP Server (Claude Desktop)</strong></summary>

Run as MCP server for Claude Desktop integration:
```bash
crossref-local serve
```

Add to Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "crossref-local": {
      "command": "crossref-local",
      "args": ["serve"],
      "env": {
        "CROSSREF_LOCAL_DB": "/path/to/crossref.db"
      }
    }
  }
}
```

Available tools:
- `search_works` - Full-text search across 167M+ papers
- `get_work` - Get paper by DOI
- `count_works` - Count matching papers
- `database_info` - Database statistics
- `calculate_impact_factor` - Journal impact factor

</details>

<details>
<summary><strong>Impact Factor</strong></summary>

```python
from crossref_local.impact_factor import ImpactFactorCalculator

with ImpactFactorCalculator() as calc:
    result = calc.calculate_impact_factor("Nature", target_year=2023)
    print(f"IF: {result['impact_factor']:.3f}")  # 54.067
```

| Journal | IF 2023 |
|---------|---------|
| Nature | 54.07 |
| Science | 46.17 |
| Cell | 54.01 |
| PLOS ONE | 3.37 |

</details>

<details>
<summary><strong>Citation Network</strong></summary>

```python
from crossref_local import get_citing, get_cited, CitationNetwork

citing = get_citing("10.1038/nature12373")  # 1539 papers
cited = get_cited("10.1038/nature12373")

# Build visualization (like Connected Papers)
network = CitationNetwork("10.1038/nature12373", depth=2)
network.save_html("citation_network.html")  # requires: pip install crossref-local[viz]
```

</details>

<details>
<summary><strong>Performance</strong></summary>

| Query | Matches | Time |
|-------|---------|------|
| `hippocampal sharp wave ripples` | 541 | 22ms |
| `machine learning` | 477,922 | 113ms |
| `CRISPR genome editing` | 12,170 | 257ms |

Searching 167M records in milliseconds via FTS5.

</details>

<details>
<summary><strong>Related Projects</strong></summary>

**[openalex-local](https://github.com/ywatanabe1989/openalex-local)** - Sister project with OpenAlex data:

| Feature | crossref-local | openalex-local |
|---------|----------------|----------------|
| Works | 167M | 284M |
| Abstracts | ~21% | ~45-60% |
| Update frequency | Real-time | Monthly |
| DOI authority | ✓ (source) | Uses CrossRef |
| Citations | Raw references | Linked works |
| Concepts/Topics | ❌ | ✓ |
| Author IDs | ❌ | ✓ |
| Best for | DOI lookup, raw refs | Semantic search |

**When to use CrossRef**: Real-time DOI updates, raw reference parsing, authoritative metadata.
**When to use OpenAlex**: Semantic search, citation analysis, topic discovery.

</details>


---

<p align="center">
  <a href="https://scitex.ai"><img src="docs/scitex-icon-navy-inverted.png" alt="SciTeX" width="40"/></a>
  <br>
  AGPL-3.0 · ywatanabe@scitex.ai
</p>

<!-- EOF -->