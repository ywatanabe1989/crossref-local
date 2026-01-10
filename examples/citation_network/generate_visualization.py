#!/usr/bin/env python3
"""Generate citation network visualization for README."""

import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from crossref_local import CitationNetwork

OUTPUT_DIR = Path(__file__).parent
DOI = "10.1038/nature12373"

print(f"Building citation network for {DOI}...")
network = CitationNetwork(DOI, depth=2, max_citing=8, max_cited=8)
print(network)

# Save HTML
html_path = OUTPUT_DIR / "citation_network.html"
network.save_html(str(html_path))
print(f"Saved: {html_path}")

# Save PNG with scitex
try:
    import scitex.plt as splt
    import networkx as nx

    G = network.to_networkx()
    fig, ax = splt.subplots(figsize=(10, 8))

    # Force-directed layout
    pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)

    # Sizes based on citation count
    sizes = [40 + min(250, math.log1p(network.nodes[n].citation_count) * 25) for n in G.nodes()]

    # Color by depth: center=blue, depth1=orange, depth2=red
    color_map = {0: '#3498db', 1: '#e67e22', 2: '#e74c3c'}
    colors = [color_map.get(network.nodes[n].depth, '#95a5a6') for n in G.nodes()]

    nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color=colors,
                           alpha=0.8, ax=ax)
    nx.draw_networkx_edges(G, pos, alpha=0.2, arrows=True, arrowsize=5,
                           edge_color='gray', ax=ax)

    ax.set_title(f"Citation Network (n={len(network.nodes)}, depth=2)")
    ax.axis("off")

    splt.savefig(OUTPUT_DIR / "citation_network.png")
    splt.close()
    print(f"Saved: {OUTPUT_DIR}/citation_network.png")

except ImportError as e:
    print(f"scitex not available: {e}")
    network.save_png(str(OUTPUT_DIR / "citation_network.png"), figsize=(10, 8))

print(f"\nNodes: {len(network.nodes)}, Edges: {len(network.edges)}")
