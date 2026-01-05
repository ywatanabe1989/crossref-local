#!/bin/bash
# Quick switcher from old to optimized rebuild script

set -e

echo "=========================================="
echo "Switch to Optimized Citations Rebuild"
echo "=========================================="
echo

# Check if old process is running
OLD_PID=$(ps aux | grep "[p]ython.*rebuild_citations_table.py" | awk '{print $2}')

if [ -n "$OLD_PID" ]; then
    echo "⚠️  Old rebuild process is still running (PID: $OLD_PID)"
    echo
    read -p "Do you want to stop it and switch to optimized version? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Stopping old process..."
        kill -INT $OLD_PID
        echo "Waiting for graceful shutdown..."
        sleep 3
        if ps -p $OLD_PID > /dev/null 2>&1; then
            echo "Process still running, forcing kill..."
            kill -9 $OLD_PID
        fi
        echo "✓ Old process stopped"
    else
        echo "Aborted. Please manually stop the old process first."
        exit 1
    fi
fi

# Check for checkpoint
CHECKPOINT_FILE="citations_rebuild_checkpoint.txt"
if [ -f "$CHECKPOINT_FILE" ]; then
    CHECKPOINT=$(cat $CHECKPOINT_FILE)
    echo "✓ Found checkpoint at offset: $CHECKPOINT"
    echo "  The optimized script will resume from here"
    echo
else
    echo "⚠️  No checkpoint found - will start fresh"
    echo
fi

# Check if running in screen
if [ -z "$STY" ]; then
    echo "⚠️  Not running in screen session"
    echo "  It's recommended to run in screen for long processes"
    echo
    read -p "Start in new screen session 'citations-rebuild-opt'? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Starting in screen..."
        screen -S citations-rebuild-opt -dm bash -c "cd /home/ywatanabe/proj/crossref_local/impact_factor/scripts/database && bash switch_to_optimized.sh --no-screen"
        echo "✓ Started in screen session 'citations-rebuild-opt'"
        echo "  Attach with: screen -r citations-rebuild-opt"
        exit 0
    fi
fi

# Change to script directory
cd /home/ywatanabe/proj/crossref_local/impact_factor/scripts/database

# Show what we're about to do
echo "About to run:"
echo "  Script: rebuild_citations_table_optimized.py"
echo "  Database: /home/ywatanabe/proj/crossref_local/data/crossref.db"
echo "  Batch size: 8192 papers"
echo "  Commit interval: 100000 papers"
echo "  Resume: YES"
echo
echo "Optimizations:"
echo "  ✓ 20GB SQLite cache (balanced with OS buffer cache)"
echo "  ✓ 8GB memory-mapped I/O"
echo "  ✓ Deferred indexing (indexes created at end)"
echo "  ✓ Large transaction batches"
echo
echo "Expected speed: ~150-200 papers/sec (vs current ~20 papers/sec)"
echo "Expected ETA: ~3-4 days (vs current ~29 days)"
echo
echo "=========================================="
echo

# Run optimized script
if [ "$1" != "--no-prompt" ]; then
    read -p "Press Enter to start..."
fi

echo "Starting optimized rebuild..."
echo

python rebuild_citations_table_optimized.py \
  --db /home/ywatanabe/proj/crossref_local/data/crossref.db \
  --batch-size 8192 \
  --commit-interval 100000 \
  --resume

echo
echo "✓ Rebuild completed!"
