<!-- ---
!-- Timestamp: 2026-01-07 23:02:46
!-- Author: ywatanabe
!-- File: /ssh:ywatanabe@nas:/home/ywatanabe/proj/crossref_local/README.md
!-- --- -->

# CrossRef Local Database

Local hosting and analysis tools for CrossRef 2025 Public Data File (167M papers, 1.4TB).

<p align="center">
  <img src="examples/impact_factor/02_compare_jcr_plot_out/scatter_calc_vs_jcr.png" alt="IF Validation" width="500"/>
</p>

## Components

| Directory | Description |
|-----------|-------------|
| [`impact_factor/`](./impact_factor/) | Journal impact factor calculator |
| [`vendor/dois2sqlite/`](./vendor/dois2sqlite/) | JSON to SQLite converter (from CrossRef Labs) |
| [`vendor/labs-data-file-api/`](./vendor/labs-data-file-api/) | REST API server (from CrossRef Labs) |
| `data/` | Database storage (gitignored) |

## Quick Start

```bash
# Calculate Impact Factor
cd impact_factor
python cli/calculate_if.py --journal "Nature" --year 2024

# Query API
curl "http://localhost:3333/api/search/?doi=10.1038/nature12373"
```

---

<details>
<summary><strong>Setup Guide</strong></summary>

### 1. Download CrossRef Data

```bash
# Download via torrent (168GB compressed)
aria2c --continue=true --max-connection-per-server=16 \
  "https://academictorrents.com/details/e0eda0104902d61c025e27e4846b66491d4c9f98"
```

### 2. Create Database

```bash
cd vendor/dois2sqlite
python3.11 -m venv .env && source .env/bin/activate
pip install -e .

# Create and load database
dois2sqlite create ./data/crossref.db
dois2sqlite load "./data/March 2025 Public Data File from Crossref" ./data/crossref.db \
  --n-jobs 8 --commit-size 100000
dois2sqlite index ./data/crossref.db
```

### 3. Run API Server

```bash
cd vendor/labs-data-file-api
python3 -m venv .env && source .env/bin/activate
pip install -r requirements.txt
ln -s ../../data/crossref.db crossref.db
python3 manage.py migrate
python main.py index-all-with-location --data-directory "../../data/March 2025 Public Data File from Crossref"
python3 manage.py runserver 0.0.0.0:3333
```

</details>

<details>
<summary><strong>Impact Factor Calculator</strong></summary>

**Results**: Strong rank correlation (Spearman r = 0.736) with JCR values across 33 journals.

**Important Limitation**: Some publishers (notably Elsevier journals like *The Lancet*, *NEJM*) don't deposit complete reference lists to CrossRef, resulting in low citation coverage (<10%) and unreliable IF calculations. Journals with >10% coverage show excellent agreement (ratio 0.96-1.46).

| Coverage | Journals | Accuracy |
|----------|----------|----------|
| >10% | Nature, Science, Cell, most neuroscience | Reliable (within 50% of JCR) |
| <10% | The Lancet, NEJM, IEEE, eLife | Unreliable (use with caution) |

Run validation: `./examples/impact_factor/run_all_demos.sh` ([sample output](examples/impact_factor/run_all_demos.sh.log))

### Setup (One-Time)

Rebuild citations table for fast IF calculations:

```bash
cd impact_factor
screen -S citations-rebuild
python scripts/database/rebuild_citations_table.py \
  --db ../data/crossref.db --batch-size 8192
# Takes 12-48 hours, reduces IF calculation from 5+ min to < 1 sec
```

### Usage

```bash
# Single journal
python cli/calculate_if.py --journal "Nature" --year 2024

# Using ISSN (faster)
python cli/calculate_if.py --issn "0028-0836" --year 2024

# Batch processing
echo -e "Nature\nScience\nCell" > journals.txt
python cli/calculate_if.py --journal-file journals.txt --year 2024 --output results.csv

# 5-year impact factor
python cli/calculate_if.py --journal "Nature" --year 2024 --window 5
```

See [impact_factor/docs/](./impact_factor/docs/) for detailed documentation.

</details>

<details>
<summary><strong>API Endpoints</strong></summary>

### Search by DOI

```bash
curl "http://localhost:3333/api/search/?doi=10.1001/.387"
```

### Search by Title

```bash
curl "http://localhost:3333/api/search/?title=deep%20learning&year=2020"
```

### Search by Author

```bash
curl "http://localhost:3333/api/search/?authors=smith&year=2020"
```

### Combined Search

```bash
curl "http://localhost:3333/api/search/?title=medicine&year=2020&authors=jones"
```

</details>

<details>
<summary><strong>Project Structure</strong></summary>

```
crossref_local/
├── README.md                 # This file
├── impact_factor/            # Impact factor calculator
│   ├── cli/                  # Command-line tools
│   ├── src/                  # Core library
│   ├── scripts/              # Database maintenance
│   ├── tests/                # Test suite
│   └── docs/                 # Documentation
├── vendor/                   # External tools (vendored)
│   ├── dois2sqlite/          # JSON to SQLite converter
│   └── labs-data-file-api/   # REST API server
├── data/                     # Database (gitignored)
│   └── crossref.db           # 1.4TB SQLite database
├── docs/                     # Root documentation
└── legacy/                   # Historical files (gitignored)
```

</details>

<details>
<summary><strong>Data Sources</strong></summary>

- **CrossRef Public Data File**: [March 2025 release](https://www.crossref.org/learning/public-data-file/)
- **Download**: [Academic Torrents](https://academictorrents.com/details/e0eda0104902d61c025e27e4846b66491d4c9f98)
- **Size**: 168GB compressed, 1.4TB database
- **Papers**: 167,008,748 records

### Vendored Dependencies

Original repositories (preserved locally in case of upstream changes):
- [gitlab.com/crossref/labs/dois2sqlite](https://gitlab.com/crossref/labs/dois2sqlite)
- [gitlab.com/crossref/labs/labs-data-file-api](https://gitlab.com/crossref/labs/labs-data-file-api)

</details>

## License

For academic and research purposes. CrossRef data usage subject to [CrossRef terms](https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-metadata-license-information/).

---

<p align="center">
  <a href="https://scitex.ai" target="_blank"><img src="docs/scitex-icon-navy-inverted.png" alt="SciTeX" width="40"/></a>
  <br>
  AGPL-3.0 · ywatanabe@scitex.ai
</p>

<!-- EOF -->