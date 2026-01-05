# CrossRef API Optimization - Next Steps After Citations Rebuild

**Created:** 2025-12-06
**Status:** Citations rebuild in progress (started Dec 4, 2025 ~22:50)
**Expected completion:** ~Dec 9-10, 2025 (5 days total)

## Quick Status Check

```bash
# From anywhere in the project:
cd ~/proj/scitex-cloud
make crossref-status        # Detailed rebuild progress
make crossref-check         # Check if complete
make crossref-next-steps    # Show next steps
```

## Current Situation

### API Status (as of Dec 6, 2025)

| Feature | Port 8000 (Django) | Port 3333 (FastAPI) |
|---------|-------------------|---------------------|
| DOI lookup | ✅ Working | ✅ Working |
| Title search | ✅ Working | ❌ Broken |
| Year search | ✅ Working | ❌ Broken |
| Author search | ✅ Working | ❌ Broken |
| Combined search | ✅ Working | ❌ Broken |

### Why Port 3333 is Broken

The FastAPI code expects separate database columns (`title`, `year`, `authors`) but the database stores everything in a JSON `metadata` column.

**Current database schema:**
```sql
CREATE TABLE works (
    id INTEGER PRIMARY KEY,
    doi TEXT,
    metadata TEXT,  -- ← All data is here as JSON
    ...
);
```

**What the FastAPI code tries to do:**
```python
# This fails because there's no 'title' column
query = "SELECT * FROM works WHERE title LIKE ?"
```

## Optimization Plan

### Step 1: Wait for Citations Rebuild to Complete ⏳

**Current progress:** Check with `make crossref-status`

**DO NOT:**
- Create new indexes during rebuild
- Modify database structure
- Run heavy database operations

**SAFE to do:**
- Use port 8000 for searches (Django API)
- Query by DOI on port 3333
- Plan the optimization steps

### Step 2: Create Search Indexes (~8-16 hours total)

**After rebuild completes**, create indexes to enable fast searches:

#### Title Index (~4-8 hours)
```bash
cd ~/proj/scitex-cloud
make crossref-create-title-index
```

Or manually:
```sql
CREATE INDEX idx_title ON works(
    json_extract(metadata, '$.title[0]')
);
```

#### Author Index (~4-8 hours)
```bash
make crossref-create-author-index
```

Or manually:
```sql
CREATE INDEX idx_author ON works(
    json_extract(metadata, '$.author')
);
```

**Note:** Year index already exists as `idx_published_year`

### Step 3: Update FastAPI Code

**File to modify:** `/home/ywatanabe/proj/scitex-cloud/deployment/crossref/database.py`

**Current code (broken):**
```python
def search_by_metadata(self, title=None, year=None, authors=None, limit=10):
    query = "SELECT * FROM works WHERE 1=1"

    if title:
        query += " AND title LIKE ?"  # ❌ No 'title' column
        params.append(f"%{title}%")
```

**Fixed code:**
```python
def search_by_metadata(self, title=None, year=None, authors=None, limit=10):
    query = "SELECT * FROM works WHERE 1=1"

    if title:
        query += " AND json_extract(metadata, '$.title[0]') LIKE ?"  # ✅ Search JSON
        params.append(f"%{title}%")

    if year:
        query += " AND json_extract(metadata, '$.published.date-parts[0][0]') = ?"
        params.append(year)

    if authors:
        query += " AND json_extract(metadata, '$.author') LIKE ?"
        params.append(f"%{authors}%")
```

### Step 4: Restart Port 3333 Service

```bash
cd ~/proj/scitex-cloud
make ENV=nas restart  # Restarts FastAPI service
```

### Step 5: Test All Search Types

```bash
# DOI lookup (should already work)
curl "http://localhost:3333/api/search/?doi=10.1001/amajethics.2018.804"

# Title search (should work after fix)
curl "http://localhost:3333/api/search/?title=machine%20learning"

# Year search (should work after fix)
curl "http://localhost:3333/api/search/?year=2018"

# Author search (should work after fix)
curl "http://localhost:3333/api/search/?authors=Smith"

# Combined search (should work after fix)
curl "http://localhost:3333/api/search/?title=machine&year=2018"
```

## Timeline

| Date | Task | Duration | Status |
|------|------|----------|--------|
| Dec 4, 2025 | Citations rebuild started | - | ⏳ In Progress |
| ~Dec 9-10 | Rebuild completes | 5 days | ⏳ Pending |
| Day 1 after | Create title index | 4-8 hours | 📅 Scheduled |
| Day 1 after | Create author index | 4-8 hours | 📅 Scheduled |
| Day 2 after | Update FastAPI code | 1 hour | 📅 Scheduled |
| Day 2 after | Test and verify | 1 hour | 📅 Scheduled |

## Performance Expectations

### Before Optimization (Port 3333)
- DOI lookup: ✅ Fast (~50ms)
- Title search: ❌ Broken
- Year search: ❌ Broken
- Author search: ❌ Broken

### After Optimization (Port 3333)
- DOI lookup: ✅ Fast (~50ms)
- Title search: ✅ Fast (~100-200ms with index)
- Year search: ✅ Fast (~100ms, index already exists)
- Author search: ✅ Fast (~100-200ms with index)
- Combined search: ✅ Fast (~200-400ms)

## Database Statistics

- **Total papers:** 167,008,748
- **Database size:** ~1.2 TB
- **Citations (after rebuild):** ~60-80 million (estimated)
- **Existing indexes:** doi, year, issn, container_title, type
- **Needed indexes:** title, author

## Existing Indexes

```sql
-- Already have these:
idx_doi_lookup              ON works(doi)
idx_published_year          ON works(json_extract(metadata, '$.published.date-parts[0][0]'))
idx_issn                    ON works(json_extract(metadata, '$.ISSN[0]'))
idx_container_title         ON works(json_extract(metadata, '$.container-title[0]'))
idx_type                    ON works(type)

-- Need to create:
idx_title                   ON works(json_extract(metadata, '$.title[0]'))
idx_author                  ON works(json_extract(metadata, '$.author'))
```

## Troubleshooting

### If citations rebuild fails:
```bash
screen -r citations-rebuild  # Attach to screen
# Check log files:
tail -f ~/proj/crossref_local/impact_factor/rebuild_citations_*.log
```

### If index creation is too slow:
- Check database isn't being accessed by other processes
- Ensure enough disk space (indexes can be large)
- Monitor with: `make crossref-status`

### If searches still don't work after updates:
1. Verify indexes exist:
   ```sql
   SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='works';
   ```
2. Check FastAPI code was updated and service restarted
3. Test with manual SQL:
   ```sql
   SELECT doi, json_extract(metadata, '$.title[0]') as title
   FROM works
   WHERE json_extract(metadata, '$.title[0]') LIKE '%test%'
   LIMIT 5;
   ```

## References

- Citations rebuild script: `~/proj/crossref_local/impact_factor/scripts/database/rebuild_citations_table.py`
- FastAPI database code: `~/proj/scitex-cloud/deployment/crossref/database.py`
- Django API (working reference): `~/proj/crossref_local/labs-data-file-api/crossrefDataFile/api.py`
- Database location: `/home/ywatanabe/proj/crossref_local/data/crossref.db`

## Quick Commands Reference

```bash
# Status and monitoring
make crossref-status           # Check rebuild progress
make crossref-check            # Check if rebuild complete
make crossref-next-steps       # Show next steps

# After rebuild completes
make crossref-create-title-index    # Create title index
make crossref-create-author-index   # Create author index

# Restart services
make ENV=nas restart           # Restart FastAPI

# Test APIs
curl "http://localhost:8000/api/search/?title=test"  # Django (always works)
curl "http://localhost:3333/api/search/?title=test"  # FastAPI (after fix)
```

## Notes

- **Do not modify database** while citations rebuild is running
- **Keep batch size at 8192** - increasing won't help much (CPU-bound)
- **Port 8000 works now** - use it for title/author/year searches during rebuild
- **Indexes take time** - be patient, they only need to be created once
- **Test thoroughly** after each step

---

*Last updated: 2025-12-06*
*Next review: After citations rebuild completes (~Dec 9-10)*
