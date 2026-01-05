# Quick Start Guide

## TL;DR - Get Impact Factor in 30 Seconds

### Method 1: Python (No containers)
```bash
cd /mnt/nas_ug/crossref_local/impact_factor
python calculate_if.py --journal "Nature" --year 2023
```

### Method 2: Docker
```bash
cd /mnt/nas_ug/crossref_local/impact_factor
docker build -t impact-factor-calculator .
./run_docker.sh --journal "Nature" --year 2023
```

### Method 3: Apptainer
```bash
cd /mnt/nas_ug/crossref_local/impact_factor
./build_apptainer.sh  # First time only
./run_apptainer.sh --journal "Nature" --year 2023
```

## Common Use Cases

### Calculate single year
```bash
python calculate_if.py --journal "Science" --year 2023
```

### Calculate time series with trend
```bash
python calculate_if.py --journal "Cell" --year 2018-2024 --moving-avg 3
```

### Save to CSV
```bash
mkdir -p output
python calculate_if.py --journal "PNAS" --year 2023 --output output/pnas.csv
```

### Batch process journals
```bash
cat > journals.txt << 'JOURNALS'
Nature
Science
Cell
PNAS
Nature Communications
JOURNALS

python calculate_if.py --journal-file journals.txt --year 2023 --output output/top5.csv
```

### Compare with JCR official data
```bash
python compare_with_jcr.py \
  --journal "Nature" \
  --year 2023 \
  --jcr-db /home/ywatanabe/proj/scitex_repo/src/scitex/scholar/data/impact_factor/impact_factor.db
```

### Calculate 5-year impact factor
```bash
python calculate_if.py --journal "Nature" --year 2023 --window 5
```

## Example Output

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

## Files Structure

```
/mnt/nas_ug/crossref_local/impact_factor/
├── calculator.py              # Core engine
├── calculate_if.py            # CLI tool
├── compare_with_jcr.py        # JCR comparison
├── test_calculator.py         # Tests
├── README.md                  # Full documentation
├── USAGE.md                   # Detailed usage examples
├── INSTALL.md                 # Installation guide
├── QUICKSTART.md              # This file
├── Dockerfile                 # Docker image
├── docker-compose.yml         # Docker compose
├── run_docker.sh              # Docker convenience script
├── impact_factor.def          # Apptainer definition
├── build_apptainer.sh         # Apptainer build script
├── run_apptainer.sh           # Apptainer convenience script
└── requirements.txt           # Python dependencies
```

## Need Help?

- Basic usage: See [USAGE.md](USAGE.md)
- Installation: See [INSTALL.md](INSTALL.md)
- Full docs: See [README.md](README.md)
- Test: Run `python test_calculator.py`
