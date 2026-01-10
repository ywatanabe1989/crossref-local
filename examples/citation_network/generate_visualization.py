#!/usr/bin/env python3
"""Generate citation network visualization for README."""

import sys
sys.path.insert(0, '../../src')

from crossref_local import CitationNetwork

# Use a well-cited paper as example
DOI = "10.1038/nature12373"  # Optogenetics paper with 1500+ citations

print(f"Building citation network for {DOI}...")
network = CitationNetwork(DOI, depth=1, max_citing=30, max_cited=20)
print(network)

# Save HTML (interactive)
html_path = "citation_network.html"
network.save_html(html_path)
print(f"Saved: {html_path}")

# Save PNG (static for README)
try:
    png_path = "citation_network.png"
    network.save_png(png_path, figsize=(14, 10))
    print(f"Saved: {png_path}")
except ImportError as e:
    print(f"PNG export requires: {e}")

print("\nNetwork stats:")
print(f"  Nodes: {len(network.nodes)}")
print(f"  Edges: {len(network.edges)}")
