#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-01-10 20:45:00 (ywatanabe)"
# File: /home/ywatanabe/proj/crossref_local/examples/citation_network/generate_visualization.py

"""Generate citation network visualization for README.

Usage:
    python generate_visualization.py
    python generate_visualization.py --doi 10.1038/nature12373 --depth 1
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import scitex as stx
import scitex.plt as splt
import networkx as nx
from crossref_local import CitationNetwork


def generate_network_plot(network, doi, output_path):
    """Generate citation network visualization."""
    G = network.to_networkx()

    # Use scitex.plt with default 40mm width
    fig, ax = splt.subplots()

    # Layout with more spacing
    pos = nx.spring_layout(G, k=3, iterations=100, seed=42)

    # Sizes (smaller nodes)
    sizes = [200 if n == doi else 80 for n in G.nodes()]

    # Colors
    colors = ["#2ecc71" if n == doi else "#3498db" for n in G.nodes()]

    # Draw edges
    nx.draw_networkx_edges(
        G, pos, alpha=0.4, edge_color="gray", arrows=True, arrowsize=12, ax=ax
    )

    # Draw nodes
    nx.draw_networkx_nodes(
        G, pos, node_size=sizes, node_color=colors, alpha=0.8, ax=ax
    )

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

    # Save with scitex - use white background (use fig.savefig for facecolor fix)
    fig.savefig(output_path, facecolor='white')
    splt.close()

    return output_path


@stx.session
def main(
    doi="10.1038/nature12373",
    depth=1,
    max_citing=6,
    max_cited=4,
    logger=stx.INJECTED,
):
    """Generate citation network visualization for README."""
    output_dir = Path(__file__).parent

    logger.info(f"Building citation network for {doi}...")
    network = CitationNetwork(doi, depth=depth, max_citing=max_citing, max_cited=max_cited)
    logger.info(f"{network}")

    # Save HTML
    html_path = output_dir / "citation_network.html"
    network.save_html(str(html_path))
    logger.info(f"Saved: {html_path}")

    # Save PNG
    png_path = output_dir / "citation_network.png"
    generate_network_plot(network, doi, png_path)
    logger.info(f"Saved: {png_path}")

    logger.info(f"Nodes: {len(network.nodes)}, Edges: {len(network.edges)}")

    return 0


if __name__ == "__main__":
    main()

# EOF
