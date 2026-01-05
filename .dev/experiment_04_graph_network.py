#!/usr/bin/env python3
"""
Experiment 4: Build a citation network graph like Connected Papers.

This combines all previous experiments:
1. Citation data extraction
2. Co-citation similarity
3. Bibliographic coupling
4. Graph building and ranking

Goal: Given a seed paper, find the top N most related papers and build a network.
"""

import sqlite3
import json
import time
from pathlib import Path
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import List, Dict, Set, Tuple

SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "../data/crossref.db"


@dataclass
class PaperNode:
    """Represents a paper in the network."""
    doi: str
    title: str = ""
    year: int = 0
    authors: List[str] = None
    similarity_score: float = 0.0


@dataclass
class NetworkEdge:
    """Represents a citation edge."""
    source: str
    target: str
    edge_type: str  # 'cites' or 'cited_by'


def print_section(title):
    """Print formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def get_paper_metadata(conn, doi):
    """Get paper metadata from works table."""
    cursor = conn.execute("SELECT metadata FROM works WHERE doi = ?", (doi,))
    row = cursor.fetchone()

    if row:
        metadata = json.loads(row[0])
        authors = metadata.get('author', [])
        author_names = [
            f"{a.get('family', '')} {a.get('given', '')[:1]}"
            for a in authors[:3]
        ]

        return PaperNode(
            doi=doi,
            title=metadata.get('title', ['Unknown'])[0][:100],
            year=metadata.get('published', {}).get('date-parts', [[0]])[0][0],
            authors=author_names
        )

    return PaperNode(doi=doi, title="Unknown")


def calculate_similarity_scores(conn, seed_doi, max_papers=50):
    """
    Calculate similarity scores for papers related to seed paper.

    Combines:
    - Bibliographic coupling (papers citing similar refs)
    - Co-citation (papers cited together)
    - Direct citations (papers that cite or are cited by seed)

    Returns dict of {doi: similarity_score}
    """
    print_section("Calculating Similarity Scores")

    scores = Counter()
    start = time.time()

    # 1. Bibliographic coupling (weight: 2x)
    print("1. Bibliographic coupling...")
    start_bc = time.time()
    cursor = conn.execute("""
        SELECT c2.citing_doi, COUNT(*) as shared_refs
        FROM citations c1
        JOIN citations c2 ON c1.cited_doi = c2.cited_doi
        WHERE c1.citing_doi = ?
          AND c2.citing_doi != ?
        GROUP BY c2.citing_doi
        ORDER BY shared_refs DESC
        LIMIT ?
    """, (seed_doi.lower(), seed_doi.lower(), max_papers))

    for doi, count in cursor:
        scores[doi] += count * 2  # Weight bibliographic coupling 2x

    bc_time = time.time() - start_bc
    print(f"   Found {len(scores)} papers in {bc_time:.2f}s")

    # 2. Co-citation (weight: 2x)
    print("2. Co-citation...")
    start_cc = time.time()
    cursor = conn.execute("""
        SELECT c2.cited_doi, COUNT(*) as cocitations
        FROM citations c1
        JOIN citations c2 ON c1.citing_doi = c2.citing_doi
        WHERE c1.cited_doi = ?
          AND c2.cited_doi != ?
        GROUP BY c2.cited_doi
        ORDER BY cocitations DESC
        LIMIT ?
    """, (seed_doi.lower(), seed_doi.lower(), max_papers))

    cocite_count = 0
    for doi, count in cursor:
        scores[doi] += count * 2  # Weight co-citation 2x
        cocite_count += 1

    cc_time = time.time() - start_cc
    print(f"   Found {cocite_count} papers in {cc_time:.2f}s")

    # 3. Direct citations (weight: 1x)
    print("3. Direct citations...")
    start_dc = time.time()

    # Papers cited by seed
    cursor = conn.execute("""
        SELECT cited_doi FROM citations WHERE citing_doi = ? LIMIT 50
    """, (seed_doi.lower(),))
    for (doi,) in cursor:
        scores[doi] += 1

    # Papers citing seed
    cursor = conn.execute("""
        SELECT citing_doi FROM citations WHERE cited_doi = ? LIMIT 50
    """, (seed_doi.lower(),))
    for (doi,) in cursor:
        scores[doi] += 1

    dc_time = time.time() - start_dc
    print(f"   Added direct citations in {dc_time:.2f}s")

    total_time = time.time() - start
    print(f"\nTotal: {len(scores)} unique papers in {total_time:.2f}s")

    return scores


def build_citation_network(conn, seed_doi, top_n=20):
    """
    Build a citation network graph around a seed paper.

    Returns:
    - nodes: List of PaperNode objects
    - edges: List of NetworkEdge objects
    """
    print_section(f"Building Citation Network (top {top_n} papers)")

    # Calculate similarity scores
    scores = calculate_similarity_scores(conn, seed_doi, max_papers=100)

    # Get top N papers
    top_papers = [seed_doi] + [doi for doi, _ in scores.most_common(top_n)]

    print(f"\nFetching metadata for {len(top_papers)} papers...")
    start = time.time()

    # Get metadata for all papers
    nodes = []
    for i, doi in enumerate(top_papers):
        node = get_paper_metadata(conn, doi)
        node.similarity_score = scores.get(doi, 100.0 if doi == seed_doi else 0.0)
        nodes.append(node)

        if (i + 1) % 5 == 0:
            print(f"  Fetched {i+1}/{len(top_papers)} papers...", end='\r')

    metadata_time = time.time() - start
    print(f"\nMetadata fetched in {metadata_time:.2f}s")

    # Build edges (citations between papers in network)
    print(f"\nBuilding citation edges...")
    start = time.time()

    paper_set = set(p.doi.lower() for p in nodes)
    edges = []

    for node in nodes:
        # Get references
        cursor = conn.execute("""
            SELECT cited_doi FROM citations
            WHERE citing_doi = ?
        """, (node.doi.lower(),))

        for (cited_doi,) in cursor:
            if cited_doi in paper_set:
                edges.append(NetworkEdge(
                    source=node.doi,
                    target=cited_doi,
                    edge_type='cites'
                ))

    edges_time = time.time() - start
    print(f"Found {len(edges)} citation edges in {edges_time:.2f}s")

    return nodes, edges


def print_network_summary(nodes, edges, seed_doi):
    """Print a summary of the network."""
    print_section("Network Summary")

    print(f"Seed paper: {seed_doi}")
    print(f"Total nodes: {len(nodes)}")
    print(f"Total edges: {len(edges)}")

    # Calculate network stats
    out_degree = Counter()
    in_degree = Counter()

    for edge in edges:
        out_degree[edge.source] += 1
        in_degree[edge.target] += 1

    print(f"\nTop 10 most related papers:")
    print(f"{'Rank':<5} {'Score':<7} {'Year':<6} {'Title':<60}")
    print("-" * 85)

    for i, node in enumerate(sorted(nodes, key=lambda n: n.similarity_score, reverse=True)[:11], 1):
        if node.doi.lower() == seed_doi.lower():
            continue
        print(f"{i:<5} {node.similarity_score:<7.1f} {node.year:<6} {node.title[:60]:<60}")

    print(f"\nTop 5 most cited (in network):")
    for doi, count in in_degree.most_common(5):
        node = next((n for n in nodes if n.doi.lower() == doi.lower()), None)
        if node:
            print(f"  {node.doi[:50]} ({count} citations): {node.title[:50]}")

    print(f"\nYear distribution:")
    year_counts = Counter(n.year for n in nodes if n.year > 0)
    for year in sorted(year_counts.keys(), reverse=True)[:10]:
        print(f"  {year}: {year_counts[year]} papers")


def export_network_json(nodes, edges, output_file):
    """Export network as JSON for visualization."""
    network_data = {
        'nodes': [
            {
                'id': node.doi,
                'title': node.title,
                'year': node.year,
                'authors': node.authors or [],
                'similarity_score': node.similarity_score
            }
            for node in nodes
        ],
        'edges': [
            {
                'source': edge.source,
                'target': edge.target,
                'type': edge.edge_type
            }
            for edge in edges
        ]
    }

    with open(output_file, 'w') as f:
        json.dump(network_data, f, indent=2)

    print(f"\nNetwork exported to: {output_file}")
    print(f"File size: {output_file.stat().st_size / 1024:.1f} KB")


def main():
    print("="*70)
    print("  Connected Papers Architecture - Experiment 4")
    print("  Citation Network Graph Building")
    print("="*70)
    print(f"\nDatabase: {DB_PATH}")

    # Test with a well-cited paper
    seed_doi = "10.1001/2013.jamapsychiatry.4"  # From experiment 2

    # Connect read-only
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)

    try:
        print(f"\nSeed paper: {seed_doi}")
        seed_node = get_paper_metadata(conn, seed_doi)
        print(f"Title: {seed_node.title}")
        print(f"Year: {seed_node.year}")

        # Build network
        nodes, edges = build_citation_network(conn, seed_doi, top_n=20)

        # Print summary
        print_network_summary(nodes, edges, seed_doi)

        # Export to JSON
        output_file = SCRIPT_DIR / "network_output.json"
        export_network_json(nodes, edges, output_file)

        # Final summary
        print_section("Experiment Complete!")
        print("✅ Citation network successfully built!")
        print("\nArchitecture validation:")
        print("  ✓ Similarity calculation works")
        print("  ✓ Network building works")
        print("  ✓ Graph export works")
        print(f"  ✓ JSON ready for visualization")
        print("\nNext steps:")
        print("  1. Optimize queries with better indexes")
        print("  2. Build web API endpoint")
        print("  3. Create frontend visualization (D3.js/vis.js)")
        print("  4. Add caching for frequently requested papers")

        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    sys.exit(main())
