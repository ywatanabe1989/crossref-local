<!-- ---
!-- Timestamp: 2025-10-13 08:18:39
!-- Author: ywatanabe
!-- File: /home/ywatanabe/proj/scitex_repo/src/scitex/scholar/crossref_local/impact_factor/scripts/README.md
!-- --- -->

# Scripts Directory

Helper scripts for the Impact Factor Calculator.

## Database Maintenance

### `maintain_indexes.sh`

Creates and maintains database indexes for optimal query performance.

**Usage:**
```bash
# Check existing indexes
./scripts/maintain_indexes.sh

# Or specify database path
./scripts/maintain_indexes.sh /path/to/crossref.db
```

**What it does:**
1. Checks which indexes exist
2. Reports missing indexes
3. Asks permission before creating indexes
4. Creates indexes with progress logging
5. Updates database statistics (ANALYZE)
6. Reports timing information

**Indexes created:**
- `idx_container_title` - For journal name lookups
- `idx_issn` - For ISSN-based searches
- `idx_published_year` - For year-based filtering
- `idx_doi_lookup` - For DOI searches
- `idx_type` - For article type filtering

**Performance impact:**
- Initial creation: Hours (for 1.1TB database)
- Query speedup: 10-100x faster
- Recommended: Run once, huge benefit

**Example output:**
```
==========================================
CrossRef Database Index Maintenance
==========================================

Database: /mnt/nas_ug/crossref_local/data/crossref.db
Database size: 1.1T

Checking existing indexes...

✓ idx_container_title exists
✓ idx_issn exists
✗ idx_published_year missing
✗ idx_doi_lookup missing
✗ idx_type missing

==========================================
Missing 3 index(es)
==========================================

Creating indexes will take a LONG time (potentially hours)
Database size: 1.1T
But queries will be MUCH faster afterward

Do you want to create missing indexes? [y/N]
```

**Running in background:**
```bash
# Run in background and log output
nohup ./scripts/maintain_indexes.sh > index_creation.log 2>&1 &

# Monitor progress
tail -f index_creation.log
```

## Container Scripts

### `build_apptainer.sh`

Builds Apptainer/Singularity container image.

**Usage:**
```bash
./scripts/build_apptainer.sh
```

### `run_apptainer.sh`

Runs calculations using Apptainer container.

**Usage:**
```bash
./scripts/run_apptainer.sh --journal "Nature" --year 2023
```

### `run_docker.sh`

Runs calculations using Docker container.

**Usage:**
```bash
./scripts/run_docker.sh --journal "Nature" --year 2023
```

### `install_apptainer.sh`

Installs Apptainer (also available at `~/.dotfiles/.bin/installers/install_apptainer.sh`).

**Usage:**
```bash
./scripts/install_apptainer.sh
```

## Tips

**First-time setup:**
```bash
# 1. Create indexes (do this first, only once)
./scripts/maintain_indexes.sh

# 2. Run test to verify everything works
cd ..
python test_calculator.py

# 3. Try a calculation
python calculate_if.py --journal "Nature" --year 2023
```

**Checking index status:**
```bash
sqlite3 /mnt/nas_ug/crossref_local/data/crossref.db \
  "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;"
```

**Removing an index (if needed):**
```bash
sqlite3 /mnt/nas_ug/crossref_local/data/crossref.db \
  "DROP INDEX IF EXISTS idx_container_title;"
```

**Database statistics:**
```bash
sqlite3 /mnt/nas_ug/crossref_local/data/crossref.db "ANALYZE;"
```

<!-- EOF -->