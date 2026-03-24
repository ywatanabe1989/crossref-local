---
package: crossref-local
skill: citations
---

# Citation Analysis

Build and visualize citation networks from the local database.

## Signatures

```python
get_citing(doi: str, limit: int = 100) -> list[str]

get_cited(doi: str, limit: int = 100) -> list[str]

get_citation_count(doi: str) -> int

class CitationNetwork:
    def __init__(
        self,
        center_doi: str,
        depth: int = 1,
        max_citing: int = 50,
        max_cited: int = 50,
    ): ...

    nodes: Dict[str, CitationNode]
    edges: List[CitationEdge]

    def save_html(self, path: str = "citation_network.html", **kwargs) -> str
    def save_png(self, path: str = "citation_network.png",
                 figsize: tuple = (12, 10)) -> str
    def to_networkx(self) -> nx.DiGraph
    def to_dict(self) -> dict
```

## `get_citing()` — Papers that Cite a DOI

Returns DOIs of papers that cite the given paper.

```python
import crossref_local as crl

citing = crl.get_citing("10.1038/nature12373", limit=50)
print(f"Cited by {len(citing)} papers")
```

## `get_cited()` — Papers a DOI Cites

Returns DOIs of papers cited by the given paper (its reference list).

```python
references = crl.get_cited("10.1038/nature12373", limit=100)
print(f"Cites {len(references)} papers")
```

## `get_citation_count()` — Count Inbound Citations

```python
n = crl.get_citation_count("10.1038/nature12373")
print(f"Cited {n} times")
```

## `CitationNetwork` — Citation Graph

Builds a directed graph of papers connected by citations, similar to
Connected Papers. Requires the `viz` extra: `pip install crossref-local[viz]`.

```python
from crossref_local import CitationNetwork

# Build network around a paper (depth=1 = direct citations only)
network = CitationNetwork("10.1038/nature12373", depth=2, max_citing=30)
print(f"Nodes: {len(network.nodes)}, Edges: {len(network.edges)}")

# Interactive HTML (requires pyvis)
network.save_html("network.html")

# Static PNG (requires matplotlib + networkx)
network.save_png("network.png", figsize=(14, 12))

# Export as dict
data = network.to_dict()
# Keys: center_doi, depth, nodes, edges, stats

# Convert to NetworkX DiGraph (requires networkx)
G = network.to_networkx()
```

## `CitationNode` Dataclass

```python
@dataclass
class CitationNode:
    doi: str
    title: str = ""
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    journal: str = ""
    citation_count: int = 0
    depth: int = 0     # 0 = center node
```

## `CitationEdge` Dataclass

```python
@dataclass
class CitationEdge:
    citing_doi: str
    cited_doi: str
    year: Optional[int] = None
```

## Notes

- Data comes from CrossRef `reference` fields — coverage varies by publisher
- `depth=2` can generate large graphs; use `max_citing` and `max_cited` to limit
- Node size in `save_html()` is proportional to `log(citation_count)`
- Node color in HTML encodes depth (red=center, blue=depth1, green=depth2…)
- `get_citing`, `get_cited`, `get_citation_count` support `@supports_return_as`
