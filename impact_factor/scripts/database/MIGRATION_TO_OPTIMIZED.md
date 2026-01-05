# Migration to Optimized Citations Rebuild

## Quick Start (Recommended)

**IMPORTANT:** The optimized script can resume from your current progress!

### Step 1: Stop the old process

```bash
# In the screen session where rebuild is running:
Ctrl+C

# The checkpoint will be saved automatically
```

### Step 2: Check the checkpoint

```bash
cat citations_rebuild_checkpoint.txt
# Should show your current offset (e.g., 19898368)
```

### Step 3: Start the optimized version with --resume

```bash
cd /home/ywatanabe/proj/crossref_local/impact_factor/scripts/database

# Start in screen
screen -S citations-rebuild-optimized

# Run optimized version with resume
python rebuild_citations_table_optimized.py \
  --db /home/ywatanabe/proj/crossref_local/data/crossref.db \
  --batch-size 8192 \
  --commit-interval 100000 \
  --resume
```

**Note:** The optimized script will:
- ✓ Read your checkpoint and resume from there
- ✓ Use the existing citations table
- ✓ Automatically DROP existing indexes (will recreate at end)
- ✓ Use 20GB cache (balanced with OS buffer cache)
- ✓ Resume inserts without index overhead (much faster!)

### Expected Performance Improvement

- **Old script**: ~20 papers/sec → ETA 29 days
- **Optimized script**: ~150-200+ papers/sec → ETA 3-4 days

**Why the improvement?**
1. No PRIMARY KEY during insert (added at the end)
2. 40GB cache instead of default
3. Larger transaction batches (100k papers per commit)
4. Memory-mapped I/O (8GB)

## Alternative: Fresh Start

If you want to start completely fresh (not recommended, you'll lose progress):

```bash
# Move old checkpoint
mv citations_rebuild_checkpoint.txt citations_rebuild_checkpoint.txt.old

# Start fresh
python rebuild_citations_table_optimized.py \
  --db /home/ywatanabe/proj/crossref_local/data/crossref.db \
  --batch-size 8192 \
  --commit-interval 100000
```

## Monitoring

### Detach and reattach
```bash
# Detach: Ctrl+A, then D
# Reattach: screen -r citations-rebuild-optimized
```

### Check progress
```bash
# View tail of log
tail -f rebuild_citations_*.log

# View current screen output
screen -S citations-rebuild-optimized -X hardcopy /tmp/screen.txt && tail -50 /tmp/screen.txt
```

## Troubleshooting

### "Database is locked"
```bash
# Check what's accessing the database
lsof /home/ywatanabe/proj/crossref_local/data/crossref.db

# Kill old process if stuck
ps aux | grep rebuild_citations_table.py
kill -9 <PID>
```

### Resume not working
```bash
# Check checkpoint file exists
ls -la citations_rebuild_checkpoint.txt

# Check citations table exists
sqlite3 /home/ywatanabe/proj/crossref_local/data/crossref.db "SELECT COUNT(*) FROM citations;"
```

## Key Differences: Old vs Optimized

| Feature | Old Script | Optimized Script |
|---------|-----------|------------------|
| Index creation | During insert (slow!) | After insert (fast!) |
| Cache size | Default (~2MB) | 40GB |
| Memory-mapped I/O | 256MB | 8GB |
| Commit interval | Every 8192 papers | Every 100,000 papers |
| Fsync | Full | Disabled during insert |
| Expected speed | ~20 papers/sec | ~150-200 papers/sec |
| ETA remaining | ~29 days | ~3-4 days |

## Safety Notes

- The optimized script uses `synchronous=OFF` during bulk insert for speed
- This is safe because we can resume from checkpoint if interrupted
- After completion, synchronous mode is restored to FULL
- Always backup important data before major operations
