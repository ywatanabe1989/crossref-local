#!/usr/bin/env python3
"""
Standalone test of the citation_graph module.

Tests the module directly without full scitex dependencies.
"""

import sys
from pathlib import Path

# Add citation_graph module to path
sys.path.insert(0, str(Path.home() / "proj/scitex-code/src"))

# Import just the citation_graph components
from scitex.scholar.citation_graph.database import CitationDatabase
from scitex.scholar.citation_graph.models import PaperNode, CitationEdge, CitationGraph
from scitex.scholar.citation_graph.builder import CitationGraphBuilder


def test_database():
    """Test database access."""
    print("\n1. Testing Database Access")
    print("-" * 60)

    db_path = Path(__file__).parent / "../data/crossref.db"
    db = CitationDatabase(str(db_path))

    with db:
        # Test forward citations
        refs = db.get_references("10.1001/2013.jamapsychiatry.4", limit=5)
        print(f"✓ Forward citations: {len(refs)} references")

        # Test reverse citations
        cites = db.get_citations("10.1001/2013.jamapsychiatry.4", limit=5)
        print(f"✓ Reverse citations: {len(cites)} citations")

        # Test co-citation
        cocited = db.get_cocited_papers("10.1001/2013.jamapsychiatry.4", limit=5)
        print(f"✓ Co-citation: {len(cocited)} papers")

        # Test metadata
        metadata = db.get_paper_metadata("10.1001/2013.jamapsychiatry.4")
        if metadata:
            print(f"✓ Metadata: {metadata.get('title', ['Unknown'])[0][:50]}")


def test_builder():
    """Test graph builder."""
    print("\n2. Testing Graph Builder")
    print("-" * 60)

    db_path = Path(__file__).parent / "../data/crossref.db"
    builder = CitationGraphBuilder(str(db_path))

    # Build small graph
    seed_doi = "10.1001/2013.jamapsychiatry.4"
    graph = builder.build(seed_doi, top_n=10)

    print(f"✓ Graph built:")
    print(f"  - Nodes: {graph.node_count}")
    print(f"  - Edges: {graph.edge_count}")
    print(f"  - Seed: {graph.seed_doi}")

    # Check nodes
    print(f"\n✓ Top 5 similar papers:")
    sorted_nodes = sorted(graph.nodes, key=lambda n: n.similarity_score, reverse=True)
    for i, node in enumerate(sorted_nodes[:5], 1):
        print(f"  {i}. [{node.year}] {node.title[:50]} (score: {node.similarity_score})")

    # Export JSON
    output_path = Path(__file__).parent / "test_graph.json"
    builder.export_json(graph, str(output_path))
    print(f"\n✓ JSON exported to: {output_path.name}")

    return graph


def test_models():
    """Test data models."""
    print("\n3. Testing Data Models")
    print("-" * 60)

    # Test PaperNode
    node = PaperNode(
        doi="10.1234/test",
        title="Test Paper",
        year=2023,
        authors=["Smith J", "Jones A"],
        similarity_score=42.0
    )
    node_dict = node.to_dict()
    print(f"✓ PaperNode: {node_dict['id']}")

    # Test CitationEdge
    edge = CitationEdge(source="10.1234/a", target="10.1234/b")
    edge_dict = edge.to_dict()
    print(f"✓ CitationEdge: {edge_dict['source']} -> {edge_dict['target']}")

    # Test CitationGraph
    graph = CitationGraph(
        seed_doi="10.1234/test",
        nodes=[node],
        edges=[edge]
    )
    graph_dict = graph.to_dict()
    print(f"✓ CitationGraph: {graph.node_count} nodes, {graph.edge_count} edges")


def main():
    print("="*70)
    print("  Citation Graph Module - Standalone Test")
    print("="*70)

    try:
        # Test individual components
        test_models()
        test_database()
        graph = test_builder()

        # Summary
        print("\n" + "="*70)
        print("  ✅ All Tests Passed!")
        print("="*70)
        print("\nModule is ready to use in scitex-cloud!")
        print("\nNext steps:")
        print("  1. Create API endpoint in scitex-cloud")
        print("  2. Build D3.js visualization")
        print("  3. Optimize database indexes")

        return 0

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
