<!-- ---
!-- Timestamp: 2025-12-05 23:50:00
!-- Author: Claude Code
!-- File: /home/ywatanabe/proj/crossref_local/impact_factor/CITATIONS_REBUILD_IMPROVEMENTS.md
!-- --- -->

# Citations Rebuild Improvements - December 5, 2024

## Summary of Improvements

This document summarizes the improvements made to the citations table rebuild process after the December 4, 2024 database lock failure.

## Problem Analysis

### What Happened (Dec 4, 2024 22:55-23:42)

1. ✅ Rebuild script started successfully
2. ✅ Found 73,044,652 papers with references (47 minutes to count)
3. ❌ Failed with "database is locked" error when attempting to backup existing table
4. Root cause: Another process had the database open

### Investigation Results

- **Current Status**: Database is NOT locked (as of Dec 5)
- **Processes Found**: No processes currently accessing the database
- **Web Services**: Running web services (uvicorn/celery) do NOT access crossref.db
- **CLI Tools**: All use proper context managers for connection handling

## Improvements Made

### 1. Enhanced Script: `rebuild_citations_table.py`

**Connection Improvements:**
```python
# Added connection timeout
conn = sqlite3.connect(db_path, timeout=30.0)

# Enabled WAL mode for better concurrency
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=30000")
```

**Lock Detection:**
- New `check_database_lock()` method
- Runs before rebuild starts
- Provides helpful error messages with resolution steps

**Retry Logic:**
- Backup operation now retries 3 times
- Exponential backoff: 1s, 2s, 4s
- Handles transient lock situations automatically

**Pre-flight Checks:**
- Database accessibility check before starting
- Clear error messages if locked
- Suggestions for resolution

### 2. New Tool: `check_db_connections.py`

**Features:**
- ✅ Tests if database is locked
- ✅ Lists processes accessing the database (using lsof)
- ✅ Shows SQLite WAL/SHM temporary files
- ✅ Provides clear status and recommendations
- ✅ Suggests exact commands to fix issues

**Usage:**
```bash
# Check database status before rebuild
python scripts/database/check_db_connections.py

# With your database
python scripts/database/check_db_connections.py --db /path/to/crossref.db
```

**Example Output:**
```
======================================================================
DATABASE CONNECTION CHECK
======================================================================
Database: /home/ywatanabe/proj/crossref_local/data/crossref.db
Size: 1.14 TB

🔍 Checking database lock status...
✅ Database is accessible (not locked)

🔍 Checking for processes accessing the database...
✅ No processes found accessing the database

🔍 Checking for SQLite WAL/SHM files...
✅ No temporary files found

======================================================================
✅ DATABASE IS READY FOR REBUILD
======================================================================
```

### 3. Updated Documentation

**`CITATIONS_TABLE_REBUILD.md` Updates:**
- Added Step 0: Check Database Status
- Enhanced troubleshooting section
- Added improvements changelog
- Better error resolution guidance

## Recommended Workflow

### Before Starting Rebuild

1. **Check database status:**
   ```bash
   python scripts/database/check_db_connections.py
   ```

2. **If locked, resolve issues:**
   - Close all SQLite browser tools
   - Close IDE database viewers
   - Kill any listed processes
   - Close Python REPL sessions

3. **Verify it's clear:**
   ```bash
   python scripts/database/check_db_connections.py
   # Should show: ✅ DATABASE IS READY FOR REBUILD
   ```

### Running the Rebuild

1. **Start screen session:**
   ```bash
   screen -S citations-rebuild
   cd /home/ywatanabe/proj/crossref_local/impact_factor
   source .venv/bin/activate
   ```

2. **Run rebuild (now with improved error handling):**
   ```bash
   python scripts/database/rebuild_citations_table.py \
     --db /home/ywatanabe/proj/crossref_local/data/crossref.db \
     --batch-size 8192
   ```

3. **Detach and monitor:**
   ```bash
   # Detach: Ctrl+A then D

   # Monitor progress:
   screen -r citations-rebuild
   tail -f rebuild_citations_*.log
   ```

## Technical Details

### Database Lock Prevention

**SQLite Connection Settings:**
- **Timeout**: 30 seconds (was immediate)
- **Journal Mode**: WAL (Write-Ahead Logging)
  - Allows concurrent reads during writes
  - Better performance for large databases
- **Busy Timeout**: 30 seconds
  - Automatically retries when database is briefly locked

**Retry Logic:**
- **Attempts**: 3 retries for critical operations
- **Backoff**: Exponential (1s → 2s → 4s)
- **Scope**: Backup operation (where failure occurred)

### Error Messages

**Before:**
```
sqlite3.OperationalError: database is locked
```

**After:**
```
❌ Database is locked: database is locked

Possible causes:
  1. Another Python script is accessing the database
  2. SQLite browser or DB tool is open
  3. Stale connection from previous session

To fix:
  - Close all programs accessing the database
  - Check for processes: lsof /path/to/crossref.db
  - Kill stale processes: ps aux | grep crossref
```

## Files Modified

1. **scripts/database/rebuild_citations_table.py**
   - Enhanced connection handling (lines 65-76)
   - Added lock detection (lines 90-114)
   - Added retry logic to backup (lines 151-179)
   - Added pre-flight check (lines 357-359)

2. **CITATIONS_TABLE_REBUILD.md**
   - Added Step 0 for pre-checks (lines 31-40)
   - Enhanced troubleshooting section (lines 218-245)

3. **scripts/database/check_db_connections.py** (NEW)
   - Full diagnostic tool for database connections
   - 170 lines of connection checking and reporting

## Next Steps

You can now proceed with the rebuild! The database is currently accessible:

```bash
# 1. Check one more time
python scripts/database/check_db_connections.py

# 2. If ready, start rebuild
screen -S citations-rebuild
cd /home/ywatanabe/proj/crossref_local/impact_factor
python scripts/database/rebuild_citations_table.py \
  --db /home/ywatanabe/proj/crossref_local/data/crossref.db \
  --batch-size 8192

# 3. Detach and let it run
# Press: Ctrl+A then D
```

## Questions?

The improvements ensure:
- ✅ Clear error messages if problems occur
- ✅ Automatic retry for transient issues
- ✅ Better concurrency with WAL mode
- ✅ Pre-flight checks before starting
- ✅ Diagnostic tools for troubleshooting

---

**Status**: Ready to retry the rebuild with improved error handling!

<!-- EOF -->
