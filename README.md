# CrossRef Local

Local CrossRef database with 167M+ scholarly works, full-text search, and impact factor calculation.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)

## Why CrossRef Local?

**Built for the LLM era** - features that matter for AI research assistants:

| Feature | Benefit |
|---------|---------|
| 📝 **Abstracts** | Full text for semantic understanding |
| 📊 **Impact Factor** | Filter by journal quality |
| 🔗 **Citations** | Prioritize influential papers |
| ⚡ **Speed** | 167M records in ms, no rate limits |

Perfect for: RAG systems, research assistants, literature review automation.

## Features

- **167M+ works** from CrossRef 2025 Public Data File
- **Full-text search** via FTS5 (search titles, abstracts, authors in milliseconds)
- **Impact factor calculation** from citation data
- **Python API** and **CLI** interface

## Installation

```bash
pip install crossref-local
```

Or from source:

```bash
git clone https://github.com/ywatanabe1989/crossref-local
cd crossref-local
make install
```

## Quick Start

### Python API

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

### CLI

```bash
# Search
crossref-local search "CRISPR genome editing" -n 5

# Get by DOI
crossref-local get 10.1038/nature12373

# Calculate impact factor
crossref-local impact-factor Nature -y 2023
# Output: Impact Factor: 54.067

# Check setup
crossref-local setup
```

<details>
<summary><strong>Impact Factor Calculation</strong></summary>

```python
from crossref_local.impact_factor import ImpactFactorCalculator

with ImpactFactorCalculator() as calc:
    result = calc.calculate_impact_factor("Nature", target_year=2023)
    print(f"IF: {result['impact_factor']:.3f}")  # 54.067
```

</details>

## Database Setup

The database is **1.5 TB** and must be built from CrossRef data files (~2 weeks).

```bash
# Check current status
crossref-local setup

# View build instructions
make db-build-info
```

<details>
<summary><strong>Build Steps</strong></summary>

1. Download CrossRef data (~100GB compressed):
   ```bash
   # Via torrent
   aria2c "https://academictorrents.com/details/..."
   ```

2. Build SQLite database:
   ```bash
   pip install dois2sqlite
   dois2sqlite build /path/to/crossref-data ./data/crossref.db
   ```

3. Build FTS5 index (~60 hours):
   ```bash
   make fts-build-screen
   ```

4. Build citations table (~days):
   ```bash
   make citations-build-screen
   ```

</details>

<details>
<summary><strong>Testing</strong></summary>

Tests use a small database downloaded from CrossRef API:

```bash
make test-db-create  # Download 500 records, build test DB
make test            # Run 22 tests (0.05s)
```

</details>

<details>
<summary><strong>Project Structure</strong></summary>

```
crossref_local/
├── src/crossref_local/     # Python package
│   ├── api.py              # search, get, count, info
│   ├── cli.py              # CLI commands
│   ├── fts.py              # Full-text search
│   ├── models.py           # Work, SearchResult
│   └── impact_factor/      # IF calculation
├── scripts/                # Database build scripts
├── tests/                  # Test suite
└── data/                   # Database (gitignored)
```

</details>

## Performance

| Query | Matches | Time |
|-------|---------|------|
| `hippocampal sharp wave ripples` | 541 | 22ms |
| `machine learning` | 477,922 | 113ms |
| `CRISPR genome editing` | 12,170 | 257ms |

Searching 167M records in milliseconds via FTS5.

## Examples

```bash
python examples/demo_wow.py      # Interactive demo
bash examples/demo_cli.sh        # CLI examples with output
```

See also: [examples/demo_wow.ipynb](examples/demo_wow.ipynb) for Jupyter notebook.

<details>
<summary><strong>Roadmap</strong></summary>

- [ ] Citation network visualization (like Connected Papers)
- [ ] Impact factor trends over time
- [ ] LangChain/LlamaIndex integrations
- [ ] Async API support

See [ROADMAP.md](ROADMAP.md) for full roadmap.

</details>

---

<p align="center">
  <a href="https://scitex.ai" target="_blank"><img src="docs/scitex-icon-navy-inverted.png" alt="SciTeX" width="40"/></a>
  <br>
  AGPL-3.0 · ywatanabe@scitex.ai
</p>
