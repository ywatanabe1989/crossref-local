# -*- mode: makefile-gmake -*-
# CrossRef Local - Root Makefile
# Thin dispatcher - delegates to scripts/
#
# Usage: make <target>
#   make status    - Show database status and health
#   make db-info   - Show database schema and row counts
#   make help      - Show all available targets

.PHONY: help status db-info db-schema db-indices fts-build fts-status \
        citations-status citations-rebuild check clean

# Paths
PROJECT_ROOT := $(shell pwd)
DB_PATH := $(PROJECT_ROOT)/data/crossref.db
SCRIPTS := $(PROJECT_ROOT)/scripts

# Default target
.DEFAULT_GOAL := help

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
