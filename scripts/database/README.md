# Database Scripts

Scripts for building and maintaining the CrossRef local database.

## Numbering Convention

| Prefix | Category |
|--------|----------|
| `00_` | Orchestration (master scripts) |
| `01_` | Step 1: Load works (uses vendor/dois2sqlite) |
| `02_` | Step 2: Create indices |
| `03_` | Step 3: Build citations table |
| `04_` | Step 4: Load journal data |
| `05_` | Step 5: Build FTS index |
| `99_` | Utilities (info, maintenance, diagnostics) |

## Build Order

```
┌─────────────────────────────────────────────────────────────┐
│  00_rebuild_all.sh  (orchestrates all steps)                │
└─────────────────────────────────────────────────────────────┘
                           │
     ┌─────────────────────┼─────────────────────┐
     ▼                     ▼                     ▼
┌─────────┐         ┌─────────────┐       ┌─────────────┐
│ Step 1  │         │   Step 2    │       │   Step 3    │
│ works   │ ──────► │  indices    │ ────► │  citations  │
│ (2-3d)  │         │  (4-8h)     │       │  (5-7d)     │
└─────────┘         └─────────────┘       └─────────────┘
                                                 │
                    ┌────────────────────────────┘
                    ▼
             ┌─────────────┐       ┌─────────────┐
             │   Step 4    │       │   Step 5    │
             │  journals   │ ────► │    FTS      │
             │  (1h)       │       │  (1-2d)     │
             └─────────────┘       └─────────────┘
```

## Scripts

### Orchestration (00_)

| Script | Description |
|--------|-------------|
| `00_rebuild_all.sh` | Master script - runs all steps in order |

### Build Steps (01_ - 05_)

| Script | Step | Description | Duration |
|--------|------|-------------|----------|
| (vendor/dois2sqlite) | 1 | Load works from Crossref data | 2-3 days |
| `02_create_missing_indexes.sh` | 2 | Create indices on works table | 4-8 hours |
| `03_rebuild_citations_table.py` | 3 | Extract citations from works | 5-7 days |
| `03_rebuild_citations_table_optimized.py` | 3 | Optimized version | 5-7 days |
| `04a_download_openalex_journals.py` | 4a | Download journal data from OpenAlex | ~30 min |
| `04b_build_issn_table.py` | 4b | Build ISSN lookup table | ~10 min |
| `04c_build_journals_table.py` | 4c | Build journals table | ~10 min |
| `04d_build_from_issn_list.py` | 4d | Build from custom ISSN list | ~10 min |
| `05_build_fts5_index.py` | 5 | Build full-text search index | 1-2 days |

### Utilities (99_)

| Script | Description |
|--------|-------------|
| `99_db_info.sh` | Show database schema, tables, indices, row counts |
| `99_maintain_indexes.sh` | Analyze and optimize indices |
| `99_check_db_connections.py` | Verify database connectivity |
| `99_switch_to_optimized.sh` | Switch to optimized table versions |

## Quick Commands

```bash
# Full rebuild (10-14 days)
make rebuild

# Show rebuild instructions
make rebuild-info

# Check prerequisites without running
make rebuild-dry-run

# Database info
make db-info

# Run individual steps
./scripts/database/00_rebuild_all.sh works
./scripts/database/00_rebuild_all.sh indices
./scripts/database/00_rebuild_all.sh citations
./scripts/database/00_rebuild_all.sh journals
./scripts/database/00_rebuild_all.sh fts
```

## Prerequisites

1. **Crossref Public Data File** (184GB)
   - Download: https://academictorrents.com/details/e4287cb7619999709f6e9db5c359dda17e93d515
   - Extract to: `data/March 2025 Public Data File from Crossref/`

2. **dois2sqlite tool**
   ```bash
   cd vendor/dois2sqlite
   pip install -e .
   ```

3. **Disk space**: 2TB+ recommended

## Output

| Table | Rows | Description |
|-------|------|-------------|
| works | ~167M | All Crossref DOIs with metadata |
| citations | ~1.79B | Citation relationships |
| journals_openalex | ~222K | Journal metadata from OpenAlex |
| issn_lookup | ~225K | ISSN to journal mapping |
| works_fts | ~167M | Full-text search index |
