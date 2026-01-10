# CrossRef Local - Roadmap

## Current Features (v0.1.0)
- [x] Full-text search via FTS5 (167M works)
- [x] DOI lookup
- [x] Impact factor calculation
- [x] Python API
- [x] CLI interface
- [x] Async API support
- [x] Citation network visualization

## Planned Features

### Graphing & Visualization
- [x] **Citation network** - Like Connected Papers
  - Get papers citing/cited by a DOI
  - Build networkx graph
  - Interactive visualization with pyvis
- [ ] **Impact factor trends** - IF over time for journals
- [ ] **Author collaboration network** - Co-authorship graphs
- [ ] **Topic clustering** - Visualize research domains

### API Enhancements
- [x] **Citation count** - `get_citation_count(doi)`
- [x] **Reference list** - `get_cited(doi)` - Get papers a DOI cites
- [x] **Citing papers** - `get_citing(doi)` - Get papers that cite a DOI
- [ ] **Batch operations** - Efficient bulk lookups

### Performance
- [x] **Async support** - `await aio.search(...)`
- [ ] **Connection pooling** - For high-throughput use
- [ ] **Cache layer** - LRU cache for frequent queries

### Integrations
- [ ] **LangChain** - Document loader for RAG
- [ ] **LlamaIndex** - Reader integration
- [ ] **Semantic Scholar** - Cross-reference with S2

## Contributing

PRs welcome! See issues for good first contributions.
