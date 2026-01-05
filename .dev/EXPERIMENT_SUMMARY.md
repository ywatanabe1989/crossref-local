# Connected Papers Architecture - Experiment Summary

**Date**: 2025-12-06
**Database**: CrossRef local (47M+ citations, 1806-2026)
**Objective**: Validate feasibility of building Connected Papers-like functionality

---

## Executive Summary

✅ **FEASIBLE** - The architecture works and can build citation networks similar to Connected Papers.

**Key Findings:**
- All core components work correctly
- Citation data extraction ✓
- Bidirectional lookups ✓
- Similarity calculations ✓
- Network graph building ✓
- JSON export for visualization ✓

**Performance Concerns:**
- Bibliographic coupling queries are slow (20-25s)
- Need index optimization for production use
- Overall network building: ~30s for top 20 papers

---

## Experiment Results

### Experiment 1: Citation Data Extraction ✅

**Purpose**: Validate basic citation data access

**Results:**
- Citations table: 47,283,173 citations indexed
- Forward citations (refs): **0.10ms** ⚡ FAST
- Reverse citations (who cites): **3,287ms** ⚠️ SLOW
- Metadata lookup: **4.66ms** ✓ Good

**Bottleneck Identified:**
- Reverse citation lookup needs optimization
- Missing or inefficient index on `cited_doi`

---

### Experiment 2: Co-citation Similarity ✅

**Purpose**: Find papers cited together (co-citation analysis)

**Results:**
- Query time: **3.23s** per paper
- Successfully ranked papers by co-citation strength
- Found papers with 11-24 co-citations (strong relationships)
- Naive vs optimized: 15/20 overlap (good consistency)

**Algorithm:**
```sql
-- Papers co-cited with target
SELECT c2.cited_doi, COUNT(*) as cocitation_count
FROM citations c1
JOIN citations c2 ON c1.citing_doi = c2.citing_doi
WHERE c1.cited_doi = ?
  AND c2.cited_doi != ?
GROUP BY c2.cited_doi
ORDER BY cocitation_count DESC
```

**Performance**: ✓ Acceptable for production

---

### Experiment 3: Bibliographic Coupling ✅

**Purpose**: Find papers with similar references

**Results:**
- Query time: **25.08s** per paper ⚠️ SLOW
- Successfully found papers with 3-4 shared references
- Combined metric (coupling + co-citation): **26.70s**
- Found 994 unique related papers

**Algorithm:**
```sql
-- Papers citing similar references
SELECT c2.citing_doi, COUNT(*) as shared_refs
FROM citations c1
JOIN citations c2 ON c1.cited_doi = c2.cited_doi
WHERE c1.citing_doi = ?
  AND c2.citing_doi != ?
GROUP BY c2.citing_doi
ORDER BY shared_refs DESC
```

**Performance**: ⚠️ Needs optimization (10x slower than co-citation)

---

### Experiment 4: Network Graph Building ✅

**Purpose**: Build complete citation network like Connected Papers

**Results:**
- Successfully built network with 21 nodes
- Similarity scoring works (combined metrics)
- JSON export ready for D3.js/vis.js
- Total build time: **29.42s** for top 20 papers

**Breakdown:**
- Bibliographic coupling: 20.97s (71%)
- Co-citation: 4.57s (16%)
- Direct citations: 3.89s (13%)
- Metadata fetch: 0.03s (<1%)

**Output Format:**
```json
{
  "nodes": [
    {
      "id": "10.1001/2013.jamapsychiatry.4",
      "title": "A Randomized Controlled Trial...",
      "year": 2013,
      "authors": ["Raison C", "Rutherford R", "Woolwine B"],
      "similarity_score": 100.0
    },
    ...
  ],
  "edges": [
    {
      "source": "doi1",
      "target": "doi2",
      "type": "cites"
    },
    ...
  ]
}
```

---

## Performance Analysis

### Current Performance

| Operation | Time | Status |
|-----------|------|--------|
| Forward citations | 0.1ms | ⚡ Excellent |
| Reverse citations | 3.3s | ⚠️ Needs optimization |
| Co-citation | 3.2s | ✓ Acceptable |
| Bibliographic coupling | 25s | ⚠️ Slow |
| Metadata lookup | 4.7ms | ✓ Good |
| **Total network build** | **~30s** | ⚠️ Acceptable but slow |

### Bottlenecks

1. **Bibliographic coupling** (71% of total time)
   - JOIN on cited_doi is slow
   - May need composite index: `(citing_doi, cited_doi)`

2. **Reverse citations** (used by co-citation)
   - Index on `cited_doi` may be missing or inefficient
   - Check: `idx_citations_cited ON citations(cited_doi, citing_year)`

### Optimization Opportunities

1. **Index improvements**
   ```sql
   -- Check if these exist and are optimal
   CREATE INDEX idx_citations_cited ON citations(cited_doi, citing_year);
   CREATE INDEX idx_citations_citing ON citations(citing_doi, cited_doi);
   CREATE INDEX idx_citations_composite ON citations(citing_doi, cited_doi, citing_year);
   ```

2. **Materialized views** for frequent queries
3. **Caching** for popular papers
4. **Parallel queries** for independent calculations
5. **Sampling** for very large result sets

---

## Architecture Validation

### ✅ What Works

1. **Citation extraction**: Access to 47M+ citation relationships
2. **Similarity metrics**: Co-citation and bibliographic coupling both work
3. **Graph building**: Can construct networks of arbitrary depth
4. **Data export**: JSON format ready for visualization
5. **Metadata access**: Fast lookup of paper details

### ⚠️ What Needs Work

1. **Performance optimization**: Bibliographic coupling is slow
2. **Index tuning**: Need better indexes on citations table
3. **Caching layer**: For frequently requested papers
4. **API endpoints**: Need to wrap in REST/GraphQL API
5. **Frontend**: Visualization layer (D3.js/vis.js)

### ❌ Missing Features

1. **Graph visualization UI**: Need interactive frontend
2. **Real-time updates**: As new citations are indexed
3. **User preferences**: Save networks, bookmarks, etc.
4. **Advanced filters**: By year, field, journal, etc.
5. **Recommendation engine**: "Papers you might like"

---

## Comparison to Connected Papers

| Feature | Connected Papers | Our Implementation | Status |
|---------|-----------------|-------------------|---------|
| Citation network | ✓ | ✓ | ✅ Done |
| Co-citation | ✓ | ✓ | ✅ Done |
| Bibliographic coupling | ✓ | ✓ | ✅ Done |
| Similarity scoring | ✓ | ✓ | ✅ Done |
| Interactive graph | ✓ | ❌ | 🔨 TODO |
| Timeline filter | ✓ | ❌ | 🔨 TODO |
| Prior/derivative works | ✓ | ✓ (partial) | ⚠️ Partial |
| Paper details | ✓ | ✓ | ✅ Done |
| Export options | ✓ | ✓ (JSON) | ✅ Done |
| Performance | <2s | ~30s | ⚠️ Needs work |

---

## Recommendations

### Immediate Next Steps

1. **Optimize indexes** on citations table
   - Run ANALYZE to update statistics
   - Add composite indexes
   - Consider partial indexes for recent years

2. **Create API endpoint**
   ```python
   @app.route('/api/network/<doi>')
   def get_network(doi):
       # Build network
       # Return JSON
   ```

3. **Add simple web frontend**
   - D3.js force-directed graph
   - Basic filtering and controls
   - Paper detail popup

### Medium-term Improvements

1. **Caching layer** (Redis)
   - Cache network graphs for popular papers
   - TTL: 24 hours (rebuild daily)

2. **Background processing**
   - Pre-compute networks for top papers
   - Async job queue (Celery)

3. **Performance targets**
   - Network build: <5s (current: ~30s)
   - API response: <2s (current: ~30s)

### Long-term Enhancements

1. **Advanced similarity metrics**
   - Topic modeling (LDA)
   - Author collaboration networks
   - Semantic similarity (embeddings)

2. **Real-time updates**
   - WebSocket for live updates
   - Incremental graph updates

3. **Machine learning**
   - Paper recommendations
   - Related field detection
   - Citation prediction

---

## Conclusion

**The Connected Papers architecture is VIABLE with current infrastructure.**

All core algorithms work correctly. The main challenge is performance optimization, particularly for bibliographic coupling queries. With proper indexing and caching, we can achieve response times under 5 seconds.

**Estimated effort to MVP:**
- Backend API: 2-3 days
- Index optimization: 1 day
- Basic frontend: 3-4 days
- **Total: ~1 week** for working prototype

**Current blockers:**
- None - all experiments passed

**Ready to proceed with implementation.**

---

## Test Files Generated

1. `experiment_01_citation_extraction.py` - Citation data access tests
2. `experiment_02_cocitation_similarity.py` - Co-citation algorithm tests
3. `experiment_03_bibliographic_coupling.py` - Bibliographic coupling tests
4. `experiment_04_graph_network.py` - Complete network building
5. `network_output.json` - Sample network output for visualization

All experiments can be re-run at any time:
```bash
python3 .dev/experiment_01_citation_extraction.py
python3 .dev/experiment_02_cocitation_similarity.py
python3 .dev/experiment_03_bibliographic_coupling.py
python3 .dev/experiment_04_graph_network.py
```
