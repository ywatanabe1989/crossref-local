# Scripts Directory

Helper scripts for CrossRef Local database management and deployment.

## Directory Structure

```
scripts/
├── database/         # Database maintenance scripts
│   ├── 00_rebuild_all.sh
│   ├── 02_create_missing_indexes.sh
│   ├── 99_db_info.sh
│   ├── 99_maintain_indexes.sh
│   └── 99_switch_to_optimized.sh
└── deployment/       # Container deployment
    ├── install_apptainer.sh
    ├── build_apptainer.sh
    ├── run_apptainer.sh
    └── run_docker.sh
```

## Database Scripts

### `database/00_rebuild_all.sh`

Full database rebuild from Crossref Public Data File.

```bash
./scripts/database/00_rebuild_all.sh --help
./scripts/database/00_rebuild_all.sh all       # Full rebuild (~10-14 days)
./scripts/database/00_rebuild_all.sh fts       # Rebuild FTS index only
```

### `database/02_create_missing_indexes.sh`

Create missing indexes on citations table.

```bash
./scripts/database/02_create_missing_indexes.sh --help
./scripts/database/02_create_missing_indexes.sh           # Default database
./scripts/database/02_create_missing_indexes.sh --dry-run # Preview changes
```

### `database/99_db_info.sh`

Display database schema, tables, indices, and row counts.

```bash
./scripts/database/99_db_info.sh --help
./scripts/database/99_db_info.sh           # Quick summary
./scripts/database/99_db_info.sh --full    # Full schema dump
./scripts/database/99_db_info.sh --tables  # Tables and counts only
```

### `database/99_maintain_indexes.sh`

Check and create missing database indexes.

```bash
./scripts/database/99_maintain_indexes.sh --help
./scripts/database/99_maintain_indexes.sh              # Check/create indexes
./scripts/database/99_maintain_indexes.sh --check-only # Only check, don't modify
```

## Deployment Scripts

### `deployment/install_apptainer.sh`

Install Apptainer container runtime.

```bash
./scripts/deployment/install_apptainer.sh --help
./scripts/deployment/install_apptainer.sh           # Install default version
./scripts/deployment/install_apptainer.sh -v 1.2.5  # Specific version
```

### `deployment/build_apptainer.sh`

Build Apptainer/Singularity container image.

```bash
./scripts/deployment/build_apptainer.sh --help
./scripts/deployment/build_apptainer.sh         # Build with defaults
./scripts/deployment/build_apptainer.sh --force # Force rebuild
```

### `deployment/run_apptainer.sh`

Run crossref-local with Apptainer container.

```bash
./scripts/deployment/run_apptainer.sh --help
./scripts/deployment/run_apptainer.sh              # Start API server
./scripts/deployment/run_apptainer.sh search CRISPR # Run search
./scripts/deployment/run_apptainer.sh shell        # Interactive shell
```

### `deployment/run_docker.sh`

Run crossref-local with Docker container.

```bash
./scripts/deployment/run_docker.sh --help
./scripts/deployment/run_docker.sh              # Start API server
./scripts/deployment/run_docker.sh search CRISPR # Run search
./scripts/deployment/run_docker.sh shell        # Interactive shell
```

## Quick Reference

**First-time setup:**
```bash
# 1. Check/create indexes (do once, takes hours)
./scripts/database/99_maintain_indexes.sh

# 2. Check database info
./scripts/database/99_db_info.sh

# 3. Run tests
make test
```

**Long-running operations:**
```bash
# Use screen for operations that take hours/days
screen -S rebuild
./scripts/database/00_rebuild_all.sh fts
# Ctrl-A D to detach
screen -r rebuild  # Reattach
```

<!-- EOF -->
