# -*- mode: makefile-gmake -*-
# CrossRef Local - Root Makefile
#
# Quick Start:
#   make install   - Install package
#   make test      - Run tests
#   make status    - Show database status

.PHONY: help install dev test status db-info db-schema db-indices fts-build fts-status \
        citations-status citations-rebuild check clean nfs-setup nfs-status nfs-stop \
        mcp-install mcp-uninstall mcp-status mcp-start mcp-stop mcp-restart mcp-logs

# Paths
PROJECT_ROOT := $(shell pwd)
DB_PATH := $(PROJECT_ROOT)/data/crossref.db
SCRIPTS := $(PROJECT_ROOT)/scripts
VENV := $(PROJECT_ROOT)/.venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

# Default target
.DEFAULT_GOAL := help

##@ Quick Start (New Users Start Here)

install: venv ## Install package (first time setup)
	@echo "Installing crossref-local..."
	@$(PIP) install -e . -q
	@echo ""
	@echo "✓ Package installed!"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Get database: make db-download  OR  make db-build"
	@echo "  2. Verify: make status"
	@echo "  3. Test: crossref-local search 'machine learning'"

venv: ## Create virtual environment
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV); \
	fi

dev: venv ## Install with dev dependencies
	@$(PIP) install -e ".[dev]" -q
	@echo "✓ Dev environment ready"

test: ## Run tests
	@$(PYTHON) -m pytest tests/ -v

test-quick: ## Run tests (quick, no output)
	@$(PYTHON) -m pytest tests/ -q

test-db-create: venv ## Download CrossRef samples and create test database
	@echo "Creating test database from CrossRef API..."
	@$(PYTHON) scripts/create_test_db.py
	@echo ""
	@echo "Test database created. Run: make test"

test-db-status: ## Check test database status
	@if [ -f "tests/fixtures/test_crossref.db" ]; then \
		echo "Test database: tests/fixtures/test_crossref.db"; \
		echo "Size: $$(du -h tests/fixtures/test_crossref.db | cut -f1)"; \
		$(PYTHON) -c "import sqlite3; c=sqlite3.connect('tests/fixtures/test_crossref.db'); print(f'Works: {c.execute(\"SELECT COUNT(*) FROM works\").fetchone()[0]}')"; \
	else \
		echo "Test database not found. Run: make test-db-create"; \
	fi

##@ Database Setup

db-info-size: ## Show database size requirements
	@echo "CrossRef Database Size"
	@echo "======================"
	@echo ""
	@echo "  Database file:     ~1.5 TB"
	@echo "  Source data:       ~100 GB (compressed)"
	@echo "  Build time:        ~2 weeks"
	@echo "  Disk space needed: ~2 TB"
	@echo ""
	@echo "Due to size, pre-built downloads are not available."
	@echo "See: make db-build-info"

db-build-info: ## Show how to build database from scratch
	@echo "Building CrossRef Database from Scratch"
	@echo "========================================"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - CrossRef data files (~100GB compressed)"
	@echo "  - ~500GB free disk space"
	@echo "  - ~2 weeks of processing time"
	@echo ""
	@echo "Steps:"
	@echo "  1. Get CrossRef data: https://www.crossref.org/blog/2023-public-data-file-now-available/"
	@echo "  2. Install dois2sqlite: pip install dois2sqlite"
	@echo "  3. Build base DB: dois2sqlite build /path/to/crossref-data ./data/crossref.db"
	@echo "  4. Build indices: make create-missing-indices"
	@echo "  5. Build FTS5: make fts-build-screen  (runs in screen, ~60 hours)"
	@echo "  6. Build citations: make citations-build-screen  (runs in screen, ~days)"
	@echo ""
	@echo "For detailed instructions: cat scripts/database/README.md"

fts-build-screen: ## Build FTS5 index in screen session (recommended)
	@echo "Starting FTS5 build in screen session 'fts-build'..."
	@screen -dmS fts-build bash -c 'cd $(PROJECT_ROOT) && $(PYTHON) $(SCRIPTS)/database/05_build_fts5_index.py 2>&1 | tee fts_build.log'
	@echo ""
	@echo "✓ Started in background!"
	@echo ""
	@echo "Commands:"
	@echo "  screen -r fts-build     # Attach to see progress"
	@echo "  Ctrl-A D                # Detach from screen"
	@echo "  tail -f fts_build.log   # Watch log file"
	@echo "  make fts-status         # Check status"

citations-build-screen: ## Build citations table in screen session
	@echo "Starting citations build in screen session 'citations-build'..."
	@screen -dmS citations-build bash -c 'cd $(PROJECT_ROOT) && $(PYTHON) $(SCRIPTS)/database/03_rebuild_citations_table_optimized.py 2>&1 | tee citations_build.log'
	@echo ""
	@echo "✓ Started in background!"
	@echo ""
	@echo "Commands:"
	@echo "  screen -r citations-build  # Attach to see progress"
	@echo "  tail -f citations_build.log"

##@ General

help: ## Show this help
	@echo "CrossRef Local - Make Targets"
	@echo "=============================="
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make \033[36m<target>\033[0m\n\n"} \
		/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)
	@echo ""
	@echo "Quick Start:"
	@echo "  make status     - Check system health"
	@echo "  make db-info    - Show database overview"

##@ Status & Information

status: ## Show overall system status (run this first!)
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║           CROSSREF LOCAL - STATUS                         ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "=== Database ==="
	@if [ -f "$(DB_PATH)" ]; then \
		echo "  ✓ Database exists: $(DB_PATH)"; \
		echo "  Size: $$(du -h "$(DB_PATH)" | cut -f1)"; \
	else \
		echo "  ✗ Database NOT FOUND: $(DB_PATH)"; \
		echo "    Hint: Check data symlink or run 'make download'"; \
	fi
	@echo ""
	@echo "=== MCP Server ==="
	@$(SCRIPTS)/mcp/status.sh
	@echo "=== NFS Server ==="
	@$(SCRIPTS)/nfs/check.sh
	@echo ""
	@echo "=== Running Processes ==="
	@ps aux | grep -E "(rebuild_citations|build_fts|sqlite3)" | grep -v grep | head -5 || echo "  No database processes running"
	@echo ""
	@echo "=== Screen Sessions ==="
	@screen -ls 2>/dev/null | grep -E "(citations|fts|rebuild)" || echo "  No relevant screen sessions"
	@echo ""
	@echo "=== Quick Stats ==="
	@if [ -f "$(DB_PATH)" ]; then \
		echo "  Works:     $$(sqlite3 "$(DB_PATH)" "SELECT stat FROM sqlite_stat1 WHERE tbl='works' LIMIT 1;" 2>/dev/null | cut -d' ' -f1 || echo '?')"; \
		echo "  Citations: $$(sqlite3 "$(DB_PATH)" "SELECT MAX(rowid) FROM citations;" 2>/dev/null || echo '?')"; \
	fi
	@echo ""
	@echo "For detailed database info: make db-info"
	@echo "For MCP server: make mcp-status"
	@echo "For NFS details: make nfs-status"

db-info: ## Show database tables, indices, and row counts
	@$(SCRIPTS)/database/99_db_info.sh

db-schema: ## Show full database schema
	@$(SCRIPTS)/database/99_db_info.sh --full

db-indices: ## Show database indices
	@$(SCRIPTS)/database/99_db_info.sh --indices

db-size: ## Show database file size
	@$(SCRIPTS)/database/99_db_info.sh --size

##@ Full-Text Search (FTS5)

fts-status: ## Check FTS index status
	@echo "=== FTS5 Index Status ==="
	@if [ -f "$(DB_PATH)" ]; then \
		count=$$(sqlite3 "$(DB_PATH)" "SELECT COUNT(*) FROM works_fts;" 2>/dev/null || echo "0"); \
		echo "  FTS entries: $$count"; \
		if [ "$$count" = "0" ]; then \
			echo "  ⚠  FTS index is EMPTY - run 'make fts-build'"; \
		fi; \
	fi

fts-build: ## Build FTS5 full-text search index (long-running)
	@echo "Starting FTS5 index build..."
	@echo "This will run in the background. Check progress with: make fts-status"
	@cd $(PROJECT_ROOT) && python3 $(SCRIPTS)/database/05_build_fts5_index.py

##@ Citations

citations-status: ## Check citations rebuild status
	@echo "=== Citations Status ==="
	@if ps aux | grep rebuild_citations_table.py | grep -v grep > /dev/null; then \
		echo "  ⏳ Rebuild is RUNNING"; \
		tail -5 rebuild_citations_*.log 2>/dev/null | grep -E "Progress|ETA" || true; \
	else \
		echo "  ✓ No rebuild in progress"; \
	fi
	@echo ""
	@sqlite3 "$(DB_PATH)" "SELECT 'Current count:', COUNT(*) FROM citations;" 2>/dev/null || echo "  Table not accessible"

citations-rebuild: ## Rebuild citations table (LONG - days)
	@echo "⚠  WARNING: This operation takes several DAYS"
	@echo "Script: $(SCRIPTS)/database/rebuild_citations_table.py"
	@echo ""
	@echo "Recommended: Run in screen session:"
	@echo "  screen -S citations-rebuild"
	@echo "  python3 $(SCRIPTS)/database/rebuild_citations_table.py"
	@echo "  Ctrl-A D (to detach)"

##@ Build / Rebuild

rebuild-info: ## Show rebuild instructions
	@$(SCRIPTS)/database/00_rebuild_all.sh --help

rebuild-dry-run: ## Check prerequisites without rebuilding
	@$(SCRIPTS)/database/00_rebuild_all.sh --dry-run all

rebuild: ## Full rebuild from Crossref data (WARNING: ~10-14 days)
	@echo "⚠️  WARNING: Full rebuild takes ~10-14 days"
	@echo "Recommend: screen -S rebuild && make rebuild-start"
	@echo ""
	@read -p "Continue? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		$(SCRIPTS)/database/00_rebuild_all.sh all; \
	else \
		echo "Cancelled."; \
	fi

##@ Maintenance

check: ## Verify database integrity
	@echo "=== Database Integrity Check ==="
	@sqlite3 "$(DB_PATH)" "PRAGMA integrity_check;" | head -5

clean: ## Clean temporary files (NOT database)
	@echo "Cleaning temporary files..."
	@find $(PROJECT_ROOT) -name "*.pyc" -delete
	@find $(PROJECT_ROOT) -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "Done. Database NOT affected."

##@ Index Management

create-missing-indices: ## Create any missing indices
	@$(SCRIPTS)/database/02_create_missing_indexes.sh

maintain-indices: ## Analyze and optimize indices
	@$(SCRIPTS)/database/99_maintain_indexes.sh

##@ MCP Server (Remote Access)

mcp-install: ## Install MCP server as systemd service
	@$(SCRIPTS)/mcp/install.sh $(if $(DB),--db $(DB),) $(if $(PORT),--port $(PORT),)

mcp-uninstall: ## Remove MCP systemd service
	@$(SCRIPTS)/mcp/install.sh --uninstall

mcp-status: ## Show MCP server status
	@$(SCRIPTS)/mcp/status.sh

mcp-start: ## Start MCP server
	@sudo systemctl start crossref-mcp
	@echo "✓ MCP server started"

mcp-stop: ## Stop MCP server
	@sudo systemctl stop crossref-mcp
	@echo "✓ MCP server stopped"

mcp-restart: ## Restart MCP server
	@sudo systemctl restart crossref-mcp
	@echo "✓ MCP server restarted"

mcp-logs: ## Show MCP server logs (live)
	@journalctl -u crossref-mcp -f

##@ NFS Server

nfs-setup: ## Setup NFS server to share database (requires .env with SUDO_PASSWORD)
	@$(SCRIPTS)/nfs/setup_nfs.sh

nfs-status: ## Show NFS server status and exports
	@$(SCRIPTS)/nfs/status.sh

nfs-stop: ## Stop NFS server
	@$(SCRIPTS)/nfs/stop.sh
