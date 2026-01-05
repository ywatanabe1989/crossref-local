# Journal Analysis Guide

## Overview

`analyze_journals.py` provides comprehensive analysis of journals in the CrossRef database, including:
- Finding unique journals
- Calculating average citation counts per paper
- Grouping statistics by year
- Comparing journals

## Quick Examples

### 1. Database Overview

```bash
python analyze_journals.py --db-stats
```

**Output:**
```
======================================================================
Database Statistics
======================================================================
Total Articles: 150,234,567
Unique Journals: 45,123
Year Range: 1950-2025
======================================================================
```

### 2. List All Unique Journals

```bash
# List all journals
python analyze_journals.py --list-journals --output all_journals.csv

# Top 100 journals by article count
python analyze_journals.py --list-journals --limit 100 --min-articles 1000

# Major journals only (1000+ articles)
python analyze_journals.py --list-journals --min-articles 1000 --output major_journals.csv
```

### 3. Analyze Specific Journal

```bash
# Overall statistics for Nature
python analyze_journals.py --journal "Nature"

# By year breakdown
python analyze_journals.py --journal "Nature" --by-year --output nature_by_year.csv

# Specific year range
python analyze_journals.py --journal "Nature" --start-year 2018 --end-year 2024 --by-year

# Use ISSN for precise matching
python analyze_journals.py --issn "0028-0836" --by-year
```

### 4. Analyze All Journals

```bash
# Top 50 journals (1000+ articles each)
python analyze_journals.py --all-journals --min-articles 1000 --limit 50 --output top50.csv

# All major journals (may take a while)
python analyze_journals.py --all-journals --min-articles 500 --output major_journals_stats.csv

# Recent years only
python analyze_journals.py --all-journals --start-year 2020 --end-year 2024 --limit 100
```

## Output Formats

### Journal List CSV

Columns:
- `journal` - Journal name
- `issn` - ISSN
- `publisher` - Publisher name
- `total_articles` - Number of articles
- `total_citations` - Sum of all citations
- `avg_citations_per_paper` - Average citations per paper
- `years_active` - Number of years with publications
- `first_year` - First publication year
- `last_year` - Most recent publication year

### Year-by-Year Statistics CSV

Columns:
- `year` - Publication year
- `journal` - Journal name
- `issn` - ISSN
- `article_count` - Articles published that year
- `total_citations` - Total citations to that year's articles
- `avg_citations` - Mean citations per paper
- `median_citations` - Median citations per paper
- `std_citations` - Standard deviation
- `min_citations`, `max_citations` - Range
- `q25_citations`, `q75_citations` - Quartiles

## Use Cases

### Find Top Cited Journals

```bash
# Analyze top 100 journals, sort by avg citations
python analyze_journals.py --all-journals --min-articles 1000 --limit 100 --output top100.csv

# Then in Python/R:
# df = pd.read_csv('top100.csv')
# df.sort_values('avg_citations_per_paper', ascending=False)
```

### Compare Journals Over Time

```bash
# Nature by year
python analyze_journals.py --journal "Nature" --by-year --output nature.csv

# Science by year
python analyze_journals.py --journal "Science" --by-year --output science.csv

# Compare in spreadsheet or Python
```

### Find Emerging Journals

```bash
# Journals with 100+ articles, recent years only
python analyze_journals.py --all-journals \
  --min-articles 100 \
  --start-year 2020 \
  --end-year 2024 \
  --output emerging.csv
```

### Field-Specific Analysis

```bash
# Find all "Neuroscience" journals
python analyze_journals.py --list-journals --output all_journals.csv
# Then filter in Excel/Python for journals containing "Neuroscience"
```

## Performance

**With indexes:**
- List journals: 10-30 seconds
- Single journal analysis: 1-5 seconds
- All journals (100+): 5-10 minutes

**Without indexes:**
- Much slower (10-100x)
- Run `./scripts/maintain_indexes.sh` first!

## Command Reference

### Modes (choose one)

- `--db-stats` - Show database overview
- `--list-journals` - List unique journals
- `--journal "Name"` - Analyze specific journal
- `--issn "XXXX-XXXX"` - Analyze by ISSN
- `--all-journals` - Analyze all journals

### Filters

- `--start-year YYYY` - Start year
- `--end-year YYYY` - End year
- `--min-articles N` - Minimum article count (default: 1)
- `--limit N` - Maximum journals to process

### Options

- `--by-year` - Group statistics by year
- `--output file.csv` - Export to CSV
- `--verbose` - Detailed logging
- `--db /path/to/db` - Custom database path

## Tips

**Finding a specific journal:**
```bash
# List all, then grep
python analyze_journals.py --list-journals | grep -i "nature"

# Or export and search in Excel
python analyze_journals.py --list-journals --output all.csv
```

**Batch analysis:**
```bash
# Create list of journals
cat > journals.txt <<EOF
Nature
Science
Cell
PNAS
Lancet
EOF

# Analyze each
while read journal; do
    python analyze_journals.py --journal "$journal" --by-year --output "${journal}.csv"
done < journals.txt
```

**Remote execution:**
```bash
# Run on NAS from local machine
ssh ugreen-nas "cd /mnt/nas_ug/crossref_local/impact_factor && \
  python analyze_journals.py --all-journals --limit 50 --output top50.csv"

# Download results
scp ugreen-nas:/mnt/nas_ug/crossref_local/impact_factor/top50.csv .
```

## Python API

```python
from analyze_journals import JournalAnalyzer

with JournalAnalyzer() as analyzer:
    # Get database stats
    stats = analyzer.get_database_stats()
    print(f"Total articles: {stats['total_articles']:,}")

    # Find top journals
    journals = analyzer.find_unique_journals(limit=100, min_articles=1000)

    # Analyze specific journal
    nature_stats = analyzer.calculate_citation_stats_by_year(
        journal_name="Nature",
        start_year=2020,
        end_year=2024
    )

    # Analyze all major journals
    all_stats = analyzer.calculate_citation_stats_all_journals(
        min_articles=1000,
        limit=50
    )
```

## Integration with Impact Factor Calculator

```bash
# Step 1: Find top journals
python analyze_journals.py --all-journals --limit 50 --output top50.csv

# Step 2: Calculate impact factors for them
cut -d',' -f1 top50.csv | tail -n +2 > journal_names.txt
python calculate_if.py --journal-file journal_names.txt --year 2023 --output if_results.csv

# Step 3: Merge and compare
# Use Python/R to join on journal name
```

## Notes

- Citation counts are current at database snapshot time (March 2025)
- Uses `is-referenced-by-count` field (fast but current totals only)
- For year-specific citations, use `calculate_if.py` with `--method reference-graph`
- Statistics include all article types (can filter in post-processing)
- Journal name matching is case-insensitive
- ISSN matching is more precise than journal name
