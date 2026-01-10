#!/usr/bin/env python3
"""Generate citation network visualization for README."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from crossref_local import CitationNetwork

OUTPUT_DIR = Path(__file__).parent
DOI = "10.1038/nature12373"

print(f"Building citation network for {DOI}...")
network = CitationNetwork(DOI, depth=1, max_citing=6, max_cited=4)
print(network)

# Save HTML
html_path = OUTPUT_DIR / "citation_network.html"
network.save_html(str(html_path))
print(f"Saved: {html_path}")

# Save PNG
try:
    import scitex.plt as splt
    import networkx as nx

    G = network.to_networkx()
    fig, ax = splt.subplots(figsize=(14, 12))

    # White background
    fig.patch.set_facecolor('white')
    ax.set_facecolor('white')

    # Layout with more spacing
    pos = nx.spring_layout(G, k=3, iterations=100, seed=42)

    # Sizes
    sizes = [500 if n == DOI else 200 for n in G.nodes()]

    # Colors
    colors = ['#2ecc71' if n == DOI else '#3498db' for n in G.nodes()]

    # Draw edges
    nx.draw_networkx_edges(G, pos, alpha=0.4, edge_color='gray',
                           arrows=True, arrowsize=12, ax=ax)

    # Draw nodes
    nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color=colors,
                           alpha=0.8, ax=ax)

    # Labels - 6pt font for inline text (scitex standard)
    labels = {}
    for n in G.nodes():
        node = network.nodes[n]
        title = node.title if node.title else "Unknown"
        short = title[:15] + "..." if len(title) > 15 else title
        labels[n] = f"{short}\n({node.year})"

    nx.draw_networkx_labels(G, pos, labels, font_size=6, ax=ax)

    ax.set_title(f"Citation Network: {len(G.nodes())} papers", fontsize=8)
    ax.axis("off")

    # Save with white background - use matplotlib directly for reliable white bg
    import matplotlib.pyplot as plt
    plt.savefig(OUTPUT_DIR / "citation_network.png", dpi=150,
                facecolor='white', edgecolor='white', bbox_inches='tight',
                pad_inches=0.1)
    plt.close()
    print(f"Saved: {OUTPUT_DIR}/citation_network.png")

except ImportError as e:
    print(f"Error: {e}")

print(f"\nNodes: {len(network.nodes)}, Edges: {len(network.edges)}")
