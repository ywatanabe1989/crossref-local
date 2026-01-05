<!-- ---
!-- Timestamp: 2025-12-04 23:12:09
!-- Author: ywatanabe
!-- File: /ssh:ywatanabe@nas:/home/ywatanabe/proj/crossref_local/impact_factor/CITATIONS_TABLE_REBUILD.md
!-- --- -->

# Citations Table Rebuild Guide

This guide provides step-by-step instructions for rebuilding the citations table to optimize Impact Factor calculations.

## Overview

**Purpose**: Build a pre-computed `citations` table with year-specific citation relationships

**Impact**: Reduces IF calculation time from 5+ minutes to < 1 second

**Duration**: 12-48 hours (one-time process)

**Database Size**: 1.2TB with 167M papers

## Prerequisites

✅ Verified database location: `/home/ywatanabe/proj/crossref_local/data/crossref.db`

✅ Sufficient disk space (database will grow ~10-20%)

✅ Python 3.11+ installed

## Starting the Rebuild

### Step 0: Check Database Status (NEW - Recommended)

Before starting the rebuild, check if the database is accessible:

```bash
# Check for database locks and active connections
python scripts/database/check_db_connections.py

# If any issues are found, follow the recommendations before proceeding
```

### Step 1: Start Screen Session

```bash
# Start a new screen session named 'citations-rebuild'
screen -S citations-rebuild

# Navigate to impact_factor directory
cd /home/ywatanabe/proj/crossref_local/impact_factor

# Python Env
python3 -m venv .venv && source .venv/bin/activate && pip install -U pip
```

### Step 2: Run the Rebuild Script

```bash
# # Run rebuild with default settings
# python scripts/database/rebuild_citations_table.py \
#   --db /home/ywatanabe/proj/crossref_local/data/crossref.db

# OR with custom batch size (adjust based on available RAM)
python scripts/database/rebuild_citations_table.py --db /home/ywatanabe/proj/crossref_local/data/crossref.db --batch-size 8192
```

### Step 3: Detach from Screen

Once the rebuild starts and you see progress messages:

1. Press `Ctrl+A` then `D` to detach
2. The rebuild continues running in the background

## Monitoring Progress

### Reattach to Screen

```bash
# List all screen sessions
screen -ls

# Reattach to the rebuild session
screen -r citations-rebuild
```

### Check Log Files

```bash
# View latest log file
cd /home/ywatanabe/proj/crossref_local/impact_factor
ls -lht rebuild_citations_*.log | head -1

# Tail the log to see real-time progress
tail -f rebuild_citations_*.log
```

### Check Checkpoint

```bash
# Check if checkpoint file exists (indicates rebuild in progress)
cat citations_rebuild_checkpoint.txt

# This shows how many papers have been processed
```

### Monitor Database

```bash
# Check citations table size
sqlite3 /home/ywatanabe/proj/crossref_local/data/crossref.db \
  "SELECT COUNT(*) FROM citations"

# Check year distribution
sqlite3 /home/ywatanabe/proj/crossref_local/data/crossref.db \
  "SELECT citing_year, COUNT(*) FROM citations GROUP BY citing_year ORDER BY citing_year DESC LIMIT 10"
```

## Expected Progress

### Timeline

| Time Elapsed | Papers Processed | Citations Inserted | Status        |
|--------------|------------------|--------------------|---------------|
| 1 hour       | ~150,000         | ~4-5M              | 0.1% complete |
| 6 hours      | ~900,000         | ~25-30M            | ~1% complete  |
| 24 hours     | ~3.6M            | ~100-120M          | ~4% complete  |
| 48 hours     | ~7.2M            | ~200-250M          | ~8% complete  |

*Note: These are estimates. Actual speed depends on hardware and reference density.*

### Log Output Example

```
2025-12-04 22:00:00 - INFO - Connected to database: /home/ywatanabe/proj/crossref_local/data/crossref.db
2025-12-04 22:00:05 - INFO - Total papers to process: 50,234,891
2025-12-04 22:00:06 - INFO - Processing papers in batches of 1,000...
2025-12-04 22:01:30 - INFO - Progress: 10,000/50,234,891 papers (0.02%) | 285,432 citations | 111.2 papers/sec | ETA: 5 days, 2:15:30
2025-12-04 22:03:00 - INFO - Progress: 20,000/50,234,891 papers (0.04%) | 571,823 citations | 222.4 papers/sec | ETA: 2 days, 14:30:15
```

## Resuming After Interruption

If the rebuild is interrupted (power loss, manual stop, etc.):

```bash
# Resume from last checkpoint
cd /home/ywatanabe/proj/crossref_local/impact_factor
screen -S citations-rebuild-resume

python scripts/database/rebuild_citations_table.py \
  --db /home/ywatanabe/proj/crossref_local/data/crossref.db \
  --resume

# Detach: Ctrl+A then D
```

## After Completion

### Verify Results

```bash
# Check total citations
sqlite3 /home/ywatanabe/proj/crossref_local/data/crossref.db \
  "SELECT COUNT(*) as total_citations FROM citations"

# Check year coverage
sqlite3 /home/ywatanabe/proj/crossref_local/data/crossref.db \
  "SELECT MIN(citing_year) as earliest, MAX(citing_year) as latest FROM citations"

# Check index status
sqlite3 /home/ywatanabe/proj/crossref_local/data/crossref.db \
  "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='citations'"
```

### Test Performance

```bash
# Test fast IF calculation
cd /home/ywatanabe/proj/crossref_local/impact_factor
time python cli/calculate_if.py --issn "0028-0836" --year 2024

# Should complete in < 1 second
```

### Cleanup

```bash
# Remove checkpoint file (if exists)
rm citations_rebuild_checkpoint.txt

# Remove old backup table (if desired)
sqlite3 /home/ywatanabe/proj/crossref_local/data/crossref.db \
  "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'citations_backup_%'"

# Optional: Drop old backup (saves space)
# sqlite3 /home/ywatanabe/proj/crossref_local/data/crossref.db \
#   "DROP TABLE citations_backup_YYYYMMDD_HHMMSS"
```

## Troubleshooting

### Rebuild is Slow

- **Check system load**: `htop` or `top`
- **Check disk I/O**: `iostat -x 5`
- **Adjust batch size**: Smaller batches use less RAM, larger batches are faster
- **Verify no other processes accessing database**

### Out of Memory

```bash
# Reduce batch size
python scripts/database/rebuild_citations_table.py \
  --db /home/ywatanabe/proj/crossref_local/data/crossref.db \
  --batch-size 500 \
  --resume
```

### Database Locked

**NEW: The rebuild script now includes automatic lock detection and retry logic!**

If you still encounter lock issues:

```bash
# Use the connection checker to diagnose
python scripts/database/check_db_connections.py

# It will show:
# - If database is locked
# - Which processes are accessing it
# - How to close them
```

Manual checks:
- Ensure no other processes are using the database
- Check for stale lock files: `lsof /path/to/crossref.db`
- Close SQLite browser tools or IDE database viewers
- Check for Python REPL sessions with open connections

**Improvements in latest version:**
- Automatic lock detection before starting
- 3 retry attempts with exponential backoff for backup operation
- 30-second connection timeout
- WAL mode for better concurrency
- Clear error messages with resolution steps

### Screen Session Lost

```bash
# Find all screen sessions
screen -ls

# If session exists, reattach
screen -r citations-rebuild

# If no session but rebuild is running
ps aux | grep rebuild_citations_table.py

# Check logs to see progress
tail -f rebuild_citations_*.log
```

## Performance Optimization

### Before Starting

1. **Close other applications** accessing the database
2. **Ensure sufficient RAM** (8GB+ recommended)
3. **Use local storage** (avoid network mounts if possible)

### During Rebuild

- Batch size of 1000-2000 works well for most systems
- Monitor system resources periodically
- Keep log files for troubleshooting

## Quick Reference Commands

```bash
# Start rebuild
screen -S citations-rebuild
python scripts/database/rebuild_citations_table.py --db /home/ywatanabe/proj/crossref_local/data/crossref.db
# Ctrl+A, D to detach

# Check progress
screen -r citations-rebuild  # Reattach
tail -f rebuild_citations_*.log  # View logs
cat citations_rebuild_checkpoint.txt  # Check checkpoint

# Resume if interrupted
python scripts/database/rebuild_citations_table.py --db /home/ywatanabe/proj/crossref_local/data/crossref.db --resume

# Test after completion
time python cli/calculate_if.py --issn "0028-0836" --year 2024
```

## Next Steps

After successful rebuild:

1. ✅ Test IF calculations (should be < 1 second)
2. ✅ Run batch processing on multiple journals
3. ✅ Set up periodic updates (monthly/quarterly) for new papers
4. ✅ Document database version and rebuild date

---

**Questions?** Check the logs first, then review this guide. The rebuild is designed to be resumable, so interruptions are not critical.

<!-- EOF -->