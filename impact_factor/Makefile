# CrossRef Local - Impact Factor Project Makefile
# Last updated: 2025-12-06

DB_PATH := /home/ywatanabe/proj/crossref_local/data/crossref.db
REBUILD_SCRIPT := scripts/database/rebuild_citations_table.py
SCREEN_NAME := citations-rebuild

.PHONY: help status check-citations-rebuild check-next-steps create-title-index create-author-index

help:
	@echo "CrossRef Local - Impact Factor Project"
	@echo "========================================"
	@echo ""
	@echo "Available targets:"
	@echo "  make status                  - Check current citations rebuild status"
	@echo "  make check-citations-rebuild - Check if citations rebuild is complete"
	@echo "  make check-next-steps        - Show next steps after citations rebuild"
	@echo "  make create-title-index      - Create index on paper titles (run AFTER rebuild)"
	@echo "  make create-author-index     - Create index on authors (run AFTER rebuild)"
	@echo ""
	@echo "⚠️  IMPORTANT REMINDER (Started: Dec 4, 2025)"
	@echo "================================================"
	@echo "Citations rebuild is running in screen session: $(SCREEN_NAME)"
	@echo "Started: Dec 4, 2025 ~22:50"
	@echo "Expected completion: ~Dec 9-10, 2025"
	@echo ""
	@echo "To check progress:"
	@echo "  screen -r $(SCREEN_NAME)"
	@echo ""
	@echo "After completion, run:"
	@echo "  make check-next-steps"
	@echo "================================================"

status:
	@echo "=== Citations Rebuild Status ==="
	@echo ""
	@echo "Screen session:"
	@screen -ls | grep $(SCREEN_NAME) || echo "❌ Screen session not found"
	@echo ""
	@echo "Process status:"
	@ps aux | grep rebuild_citations_table.py | grep -v grep || echo "❌ Process not running"
	@echo ""
	@echo "Latest log entries:"
	@tail -20 rebuild_citations_*.log 2>/dev/null | grep -E "Progress|ETA" | tail -5 || echo "No log found"
	@echo ""
	@echo "Database size:"
	@du -h $(DB_PATH) 2>/dev/null || echo "Database not found"
	@echo ""
	@echo "Citations table row count:"
	@sqlite3 $(DB_PATH) "SELECT COUNT(*) as count FROM citations;" 2>/dev/null | awk '{print "  " $$0 " citations"}' || echo "  Table not accessible"

check-citations-rebuild:
	@echo "=== Checking Citations Rebuild Completion ==="
	@echo ""
	@# Check if rebuild script is still running
	@if ps aux | grep rebuild_citations_table.py | grep -v grep > /dev/null; then \
		echo "⏳ Citations rebuild is STILL RUNNING"; \
		echo ""; \
		echo "Current progress:"; \
		tail -20 rebuild_citations_*.log 2>/dev/null | grep Progress | tail -1; \
		echo ""; \
		echo "Run 'make status' for detailed status"; \
		echo ""; \
		echo "❌ NOT READY for next steps yet"; \
	else \
		echo "✅ Citations rebuild appears to be COMPLETE!"; \
		echo ""; \
		echo "Verification:"; \
		sqlite3 $(DB_PATH) "SELECT COUNT(*) FROM citations;" | awk '{print "  Total citations: " $$0}'; \
		echo ""; \
		echo "✅ Ready for next steps!"; \
		echo ""; \
		echo "Run: make check-next-steps"; \
	fi

check-next-steps:
	@echo "=== Next Steps After Citations Rebuild ==="
	@echo ""
	@echo "The citations rebuild is complete. Next optimizations:"
	@echo ""
	@echo "1. 📊 Create Title Index (enables fast title search on port 3333)"
	@echo "   Command: make create-title-index"
	@echo "   Time: ~4-8 hours"
	@echo "   Benefit: Fast title searches via FastAPI (port 3333)"
	@echo ""
	@echo "2. 👥 Create Author Index (enables fast author search on port 3333)"
	@echo "   Command: make create-author-index"
	@echo "   Time: ~4-8 hours"
	@echo "   Benefit: Fast author searches via FastAPI (port 3333)"
	@echo ""
	@echo "3. 🔧 Update FastAPI Code"
	@echo "   Location: /home/ywatanabe/proj/scitex-cloud/deployment/crossref/database.py"
	@echo "   Update search_by_metadata() to use JSON queries"
	@echo "   See: docs/API_OPTIMIZATION.md"
	@echo ""
	@echo "Current API status:"
	@echo "  Port 8000 (Django):  ✅ All searches work (DOI, title, year, authors)"
	@echo "  Port 3333 (FastAPI): ⚠️  Only DOI works, title/author broken (no indexes)"
	@echo ""
	@echo "For details, see: NEXT_STEPS_AFTER_REBUILD.md"

create-title-index:
	@echo "=== Creating Title Index ==="
	@echo ""
	@echo "⚠️  WARNING: This will take 4-8 hours"
	@echo "⚠️  Do NOT interrupt or run other DB operations during this time"
	@echo ""
	@read -p "Continue? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		echo ""; \
		echo "Starting index creation..."; \
		echo ""; \
		sqlite3 $(DB_PATH) "CREATE INDEX IF NOT EXISTS idx_title ON works(json_extract(metadata, '\$$.title[0]'));" && \
		echo "✅ Title index created successfully!" || \
		echo "❌ Error creating index"; \
	else \
		echo "Cancelled."; \
	fi

create-author-index:
	@echo "=== Creating Author Index ==="
	@echo ""
	@echo "⚠️  WARNING: This will take 4-8 hours"
	@echo "⚠️  Do NOT interrupt or run other DB operations during this time"
	@echo ""
	@read -p "Continue? (yes/no): " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		echo ""; \
		echo "Starting index creation..."; \
		echo ""; \
		sqlite3 $(DB_PATH) "CREATE INDEX IF NOT EXISTS idx_author ON works(json_extract(metadata, '\$$.author'));" && \
		echo "✅ Author index created successfully!" || \
		echo "❌ Error creating index"; \
	else \
		echo "Cancelled."; \
	fi
