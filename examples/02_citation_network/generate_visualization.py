#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-01-11 (ywatanabe)"
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
import figrecipe as fr
from crossref_local import CitationNetwork

# Load SCITEX style with white background
fr.load_style("SCITEX", background="white")


def generate_network_plot(network, doi, output_path):
    """Generate citation network visualization using figrecipe."""
    G = network.to_networkx()

    # Add node attributes for styling
    for n in G.nodes():
        node = network.nodes[n]
        title = node.title if node.title else "Unknown"
        short = title[:15] + "..." if len(title) > 15 else title
        G.nodes[n]["label"] = f"{short}\n({node.year})"
        G.nodes[n]["is_root"] = (n == doi)

    # Use figrecipe defaults
    fig, ax = fr.subplots()

    # Draw graph with figrecipe's graph() method
    ax.graph(
        G,
        layout="spring",
        seed=42,
        # Node styling - root node larger and green
        node_size=lambda n, d: 200 if d.get("is_root") else 80,
        node_color=lambda n, d: "#2ecc71" if d.get("is_root") else "#3498db",
        node_alpha=0.8,
        # Edge styling
        edge_alpha=0.4,
        edge_color="gray",
        arrows=True,
        arrowsize=12,
        # Labels
        labels="label",
        font_size=6,
        # Layout parameters
        k=3,
        iterations=100,
    )

    ax.set_title("Citation Network Demo")

    # Set panel caption for composition (without panel letter - added during composition)
    ax.set_caption("Citation network built from local CrossRef database")

    # Save using fr.save() for proper mm layout and auto-cropping
    fr.save(fig, output_path, validate=False, verbose=False)

    return output_path


@stx.session
def main(
    doi="10.1038/nature12373",
    depth=1,
    max_citing=8,
    max_cited=6,
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
