# CrossRef Local - Roadmap

## Current Features (v0.1.0)
- [x] Full-text search via FTS5 (167M works)
- [x] DOI lookup
- [x] Impact factor calculation
- [x] Python API
- [x] CLI interface

## Planned Features

### Graphing & Visualization
- [ ] **Citation network** - Like Connected Papers
  - Get papers citing/cited by a DOI
  - Build networkx graph
  - Interactive visualization with pyvis
- [ ] **Impact factor trends** - IF over time for journals
- [ ] **Author collaboration network** - Co-authorship graphs
- [ ] **Topic clustering** - Visualize research domains

### API Enhancements
- [ ] **Citation count** - `work.citation_count` property
- [ ] **Reference list** - Get papers a DOI cites
- [ ] **Citing papers** - Get papers that cite a DOI
- [ ] **Batch operations** - Efficient bulk lookups

### Performance
- [ ] **Async support** - `await search(...)`
- [ ] **Connection pooling** - For high-throughput use
- [ ] **Cache layer** - LRU cache for frequent queries

### Integrations
- [ ] **LangChain** - Document loader for RAG
- [ ] **LlamaIndex** - Reader integration
- [ ] **Semantic Scholar** - Cross-reference with S2

## Contributing

PRs welcome! See issues for good first contributions.
