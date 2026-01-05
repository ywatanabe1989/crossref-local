<!-- ---
!-- Timestamp: 2025-12-06 04:30:57
!-- Author: ywatanabe
!-- File: /ssh:ywatanabe@nas:/home/ywatanabe/proj/crossref_local/impact_factor/README.md
!-- --- -->

# Impact Factor Calculator

Calculate journal impact factors directly from your local CrossRef database with optimized performance.

## Quick Start

### Basic Usage

```bash
# Calculate 2-year IF for a specific journal
cd /home/ywatanabe/proj/crossref_local/impact_factor
python cli/calculate_if.py --journal "Nature" --year 2024

# Using ISSN (faster)
python cli/calculate_if.py --issn "0028-0836" --year 2024

# Batch process multiple journals
echo -e "Nature\nScience\nCell" > journals.txt
python cli/calculate_if.py --journal-file journals.txt --year 2024 --output results.csv
```

## Directory Structure

```
impact_factor/
├── src/                       # Core library
│   ├── __init__.py
│   └── calculator.py          # ImpactFactorCalculator class
│
├── cli/                       # Command-line tools
│   ├── calculate_if.py        # Main IF calculator
│   ├── analyze_journals.py    # Journal statistics
│   └── compare_with_jcr.py    # JCR comparison
│
├── scripts/                   # Maintenance & deployment
│   ├── database/              # Database maintenance
│   │   ├── rebuild_citations_table.py    # Rebuild citations table
│   │   └── maintain_indexes.sh           # Index maintenance
│   └── deployment/            # Container deployment
│       ├── build_apptainer.sh
│       └── run_docker.sh
│
├── tests/                     # Test suite
│   └── test_calculator.py
│
├── docs/                      # Documentation
│   ├── QUICKSTART.md
│   ├── INSTALL.md
│   └── USAGE.md
│
├── legacy/                    # Old/deprecated files
│
└── data -> ../data/           # Symlink to database
```

## Database Optimization

### One-Time Setup: Rebuild Citations Table

For optimal performance, rebuild the citations table once to enable fast IF calculations:

```bash
# Start in screen session (recommended for long-running process)
cd /home/ywatanabe/proj/crossref_local/impact_factor
screen -S citations-rebuild

# Run rebuild (takes 12-48 hours for full database)
python scripts/database/rebuild_citations_table.py --db /home/ywatanabe/proj/crossref_local/data/crossref.db --batch-size 8192

# Detach from screen: Ctrl+A then D
# Reattach later: screen -r citations-rebuild
```

This creates an optimized `citations` table that reduces IF calculation time from 5+ minutes to < 1 second.

### Index Maintenance

```bash
# Check and create necessary indexes
cd /home/ywatanabe/proj/crossref_local/impact_factor
./scripts/database/maintain_indexes.sh
```

## Features

- **Fast calculations**: < 1 second per journal (after citations table rebuild)
- **Flexible timeframes**: 2-year, 5-year impact factors
- **Time series analysis**: Moving averages, trend analysis
- **Batch processing**: Calculate multiple journals efficiently
- **Multiple methods**: Fast (pre-computed) vs. accurate (reference-graph)
- **No API limits**: All queries run on local database

## Performance

| Operation | Before Optimization | After Optimization |
|-----------|--------------------|--------------------|
| Nature 2024 IF | 5+ min (timeout) | < 1 second |
| Batch 100 journals | Hours | Minutes |
| Database queries | JSON parsing | Indexed lookups |

## Example Usage

```bash
# Single journal, single year
python cli/calculate_if.py --journal "Nature" --year 2024

# Time series with moving average
python cli/calculate_if.py --journal "Cell" --year 2020-2024 --moving-avg 3

# 5-year impact factor
python cli/calculate_if.py --issn "0028-0836" --year 2024 --window 5

# Compare with JCR official data
python cli/compare_with_jcr.py --journal "Nature" --year 2023 \
  --jcr-db /path/to/jcr/impact_factor.db
```

## Requirements

- CrossRef database: `/home/ywatanabe/proj/crossref_local/data/crossref.db`
- Python 3.11+
- Dependencies: numpy (see `requirements.txt`)

## Documentation

- [Quick Start Guide](docs/QUICKSTART.md)
- [Installation Guide](docs/INSTALL.md)
- [Usage Examples](docs/USAGE.md)
- [Apptainer Setup](docs/INSTALL_APPTAINER.md)

## Citation Data Source

- CrossRef Public Data File (March 2025)
- Database size: 1.2TB, 167M papers
- Last updated: October 13, 2024

## License

For academic and research purposes. CrossRef data usage subject to CrossRef terms.

<!-- EOF -->