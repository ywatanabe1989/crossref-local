#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2026-01-11 (ywatanabe)"
# File: /home/ywatanabe/proj/crossref_local/examples/compose_readme.py

"""Compose README figure from existing recipes using figrecipe.

Uses fr.compose() to combine IF validation and citation network figures.
Captions are read from YAML recipes (single source of truth) and panel
letters are added programmatically during composition.
"""

import string
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import figrecipe as fr

fr.load_style("SCITEX", background="white")

base = Path(__file__).parent

# Define sources (YAML files are single source of truth)
sources = {
    (0, 0): base / "impact_factor/02_compare_jcr_plot_out/scatter_calc_vs_jcr.yaml",
    (0, 1): base / "citation_network/citation_network.yaml",
}

# Compose from YAML recipes
fig, axes = fr.compose(layout=(1, 2), sources=sources)

# Add panel labels (A, B)
fig.add_panel_labels()

# Build caption programmatically from YAML sources
# Each source YAML has ax_0_0 (single panel), we read caption from there
panel_letters = string.ascii_uppercase
panel_captions = []

for idx, ((row, col), yaml_path) in enumerate(sorted(sources.items())):
    with open(yaml_path) as f:
        recipe = yaml.safe_load(f)
    # Get caption from first axes in source (each source is single-panel)
    axes_data = recipe.get("axes", {})
    # Source files have ax_0_0 regardless of target position
    ax_data = axes_data.get("ax_0_0", {})
    caption = ax_data.get("caption", "")
    if caption:
        letter = panel_letters[idx]
        panel_captions.append(f"({letter}) {caption}")

# Construct full figure caption
figure_title = "Figure 1. CrossRef Local validation and demonstration."
caption_text = f"{figure_title} " + " ".join(panel_captions)

# Set figure-level caption and render it
fig.set_caption(caption_text)
fig.render_caption()

# Save (background='white' set in load_style)
output = base / "readme_figure.png"
fig.savefig(output, verbose=False)
print(f"Composed: {output}")
print(f"Caption: {fig.caption}")

# EOF
