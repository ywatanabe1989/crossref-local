# Impact Factor Calculator from CrossRef Local Database

This module calculates journal impact factors directly from the local CrossRef database.

## Features

- Calculate classic 2-year Journal Impact Factor (JIF)
- Calculate 5-year impact factor
- Moving average analysis for trends
- Compare with official JCR values
- Fast local database queries (no API limits)
- Citation network analysis

## Components

- `calculator.py`: Core impact factor calculation engine
- `calculate_if.py`: CLI tool for calculating impact factors
- `compare_with_jcr.py`: Compare calculated vs official JCR values
- `analyze_trends.py`: Generate trend analysis and visualizations

## Usage

### Basic Impact Factor Calculation

```bash
# Calculate IF for Nature journal
python calculate_if.py --journal "Nature" --year 2023

# Calculate for multiple years
python calculate_if.py --journal "Nature" --year 2020-2024

# Calculate with moving average
python calculate_if.py --journal "Nature" --year 2020-2024 --moving-avg 3
```

### Compare with JCR

```bash
# Compare calculated IF with official JCR data
python compare_with_jcr.py --journal "Nature" --year 2023 \
  --jcr-db /path/to/jcr/impact_factor.db
```

### Batch Processing

```bash
# Calculate IF for multiple journals from file
python calculate_if.py --journal-file journals.txt --year 2023 --output results.csv
```

## How It Works

### Impact Factor Formula

**2-Year IF:**
```
IF(2024) = Citations in 2024 to articles published in 2022-2023
           / Articles published in 2022-2023
```

**5-Year IF:**
```
IF(2024) = Citations in 2024 to articles published in 2019-2023
           / Articles published in 2019-2023
```

### Data Sources

1. **Article counts**: From `works` table filtered by journal and year
2. **Citation counts**: Two methods:
   - Method 1 (fast): Use `is-referenced-by-count` field
   - Method 2 (accurate): Build citation graph from `reference` fields

## Database Requirements

- CrossRef local database at: `/mnt/nas_ug/crossref_local/data/crossref.db`
- Recommended indexes:
  ```sql
  CREATE INDEX idx_container_title ON works(json_extract(metadata, '$.container-title[0]'));
  CREATE INDEX idx_issn ON works(json_extract(metadata, '$.ISSN[0]'));
  CREATE INDEX idx_published_year ON works(json_extract(metadata, '$.published.date-parts[0][0]'));
  ```

## Output Format

CSV with columns:
- journal
- issn
- year
- articles_current_year
- articles_previous_year
- articles_2year_window
- citations_to_2year_window
- impact_factor_2year
- impact_factor_5year
- moving_avg_3year
- calculation_method

## Performance

- Single journal/year: ~1-5 seconds
- Batch processing: Parallel execution available
- Cache results for repeated queries

## Dependencies

- sqlite3
- pandas
- numpy (for moving averages)
