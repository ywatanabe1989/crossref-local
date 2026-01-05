# Impact Factor Calculator - Usage Guide

## Quick Start

### Option 1: Direct Python Execution (if dependencies installed)

```bash
cd /mnt/nas_ug/crossref_local/impact_factor

# Single journal, single year
python calculate_if.py --journal "Nature" --year 2023

# Year range with moving average
python calculate_if.py --journal "Nature" --year 2020-2024 --moving-avg 3 --output nature_if.csv

# Use ISSN for precise matching
python calculate_if.py --issn "0028-0836" --year 2023

# Calculate 5-year impact factor
python calculate_if.py --journal "Nature" --year 2023 --window 5
```

### Option 2: Docker (Recommended - No local dependencies needed)

```bash
cd /mnt/nas_ug/crossref_local/impact_factor

# Build Docker image (first time only)
docker build -t impact-factor-calculator .

# Run calculations
./run_docker.sh --journal "Nature" --year 2023

# Or use docker run directly
docker run --rm \
  -v /mnt/nas_ug/crossref_local/data:/data:ro \
  -v $(pwd)/output:/output \
  impact-factor-calculator \
  python calculate_if.py --journal "Nature" --year 2023 --output /output/nature_if.csv
```

### Option 3: Docker Compose

```bash
cd /mnt/nas_ug/crossref_local/impact_factor

# Start container in background
docker-compose up -d

# Run calculations in running container
docker-compose exec impact-factor python calculate_if.py --journal "Nature" --year 2023

# Stop container
docker-compose down
```

## Examples

### Example 1: Calculate Nature Impact Factor for 2023

```bash
python calculate_if.py --journal "Nature" --year 2023
```

**Expected Output:**
```
======================================================================
Journal: Nature
Target Year: 2023
Window: 2021-2022 (2 years)
Method: is-referenced-by
----------------------------------------------------------------------
Articles published in window: 2847
  By year:
    2021: 1423 articles
    2022: 1424 articles
----------------------------------------------------------------------
Citations to window articles: 142350
Impact Factor: 50.015
======================================================================
```

### Example 2: Time Series with Moving Average

```bash
python calculate_if.py --journal "Nature" --year 2018-2024 --moving-avg 3 --output nature_trend.csv
```

### Example 3: Batch Process Multiple Journals

Create `journals.txt`:
```
Nature
Science
Cell
PNAS
Nature Communications
```

Run:
```bash
python calculate_if.py --journal-file journals.txt --year 2023 --output top_journals_2023.csv
```

### Example 4: Compare with Official JCR Data

```bash
python compare_with_jcr.py \
  --journal "Nature" \
  --year 2023 \
  --jcr-db /home/ywatanabe/proj/scitex_repo/src/scitex/scholar/data/impact_factor/impact_factor.db \
  --output comparison.csv
```

**Expected Output:**
```
======================================================================
Journal: Nature
Year: 2023
----------------------------------------------------------------------
Calculated IF: 50.015
Official JCR IF: 49.962
Difference: +0.053
Percent Difference: +0.1%
Status: ✓ Excellent agreement
======================================================================
```

### Example 5: Use Reference-Graph Method (More Accurate but Slower)

```bash
python calculate_if.py \
  --journal "Nature" \
  --year 2023 \
  --method reference-graph \
  --verbose
```

**Note:** This method builds a citation graph by parsing all reference fields, which is more accurate but significantly slower.

## Calculation Methods

### Method 1: `is-referenced-by` (Default - Fast)

- Uses the `is-referenced-by-count` field from CrossRef metadata
- Fast queries (seconds)
- Returns current total citations (not year-specific)
- **Best for:** Quick estimates, recent trends

### Method 2: `reference-graph` (Accurate but Slow)

- Builds citation graph from `reference` fields
- Respects citation year for accurate IF calculation
- Much slower (minutes to hours depending on journal size)
- **Best for:** Accurate historical analysis, validation

## Output Formats

### Console Output (Default)
Human-readable formatted text with all details

### CSV Output (--output file.csv)
Structured data with columns:
- journal
- target_year
- window_years
- window_range
- total_articles
- total_citations
- impact_factor
- moving_average (if calculated)
- method
- status

## Performance Tips

1. **Use ISSN for precise matching**: Avoids ambiguity with similar journal names
2. **Use `is-referenced-by` method first**: Get quick estimates before running slower analyses
3. **Batch process with --journal-file**: More efficient than individual runs
4. **Add database indexes** for better performance:
   ```bash
   sqlite3 /mnt/nas_ug/crossref_local/data/crossref.db <<EOF
   CREATE INDEX IF NOT EXISTS idx_container_title
     ON works(json_extract(metadata, '$.container-title[0]'));
   CREATE INDEX IF NOT EXISTS idx_issn
     ON works(json_extract(metadata, '$.ISSN[0]'));
   CREATE INDEX IF NOT EXISTS idx_published_year
     ON works(json_extract(metadata, '$.published.date-parts[0][0]'));
   EOF
   ```

## Troubleshooting

### Issue: "No articles found"
- Check journal name spelling
- Try using ISSN instead: `--issn "0028-0836"`
- Verify year range is valid

### Issue: "Database not found"
- Verify database path: `/mnt/nas_ug/crossref_local/data/crossref.db`
- Use `--db` flag to specify custom path

### Issue: Slow performance
- Add database indexes (see Performance Tips)
- Use `is-referenced-by` method instead of `reference-graph`
- Consider batch processing for multiple queries

### Issue: Docker permission errors
- Ensure data directory has read permissions
- Check output directory exists and is writable
- Run with appropriate user: `docker run --user $(id -u):$(id -g) ...`

## Remote Execution

Since this is on the NAS, you can run remotely via SSH:

```bash
# From your local machine
ssh ugreen-nas "cd /mnt/nas_ug/crossref_local/impact_factor && python calculate_if.py --journal 'Nature' --year 2023"

# Or using Docker
ssh ugreen-nas "cd /mnt/nas_ug/crossref_local/impact_factor && ./run_docker.sh --journal 'Nature' --year 2023"
```

## Python API Usage

For programmatic access:

```python
from calculator import ImpactFactorCalculator

with ImpactFactorCalculator() as calc:
    # Single year
    result = calc.calculate_impact_factor(
        journal_identifier="Nature",
        target_year=2023,
        window_years=2
    )

    print(f"Impact Factor: {result['impact_factor']:.3f}")

    # Time series
    results = calc.calculate_if_time_series(
        journal_identifier="Nature",
        start_year=2018,
        end_year=2024,
        window_years=2
    )

    # Moving average
    results = calc.calculate_moving_average(results, window=3)
```

## Known Limitations

1. **Recent articles**: Citations to very recent articles may be underreported
2. **Database coverage**: Limited to journals in CrossRef database
3. **Citation delay**: New citations may take time to appear in database
4. **Self-citations**: Not filtered (same as official JCR)
5. **Article types**: Only counts `journal-article` type (same as JCR)

## Citation

If you use this tool in research, please cite:
- CrossRef database: https://www.crossref.org/
- Your local database version: March 2025 Public Data File
