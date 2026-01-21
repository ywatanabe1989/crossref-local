"""Visualization tools for cache analysis.

Provides plotting and network visualization for cached paper collections.

Usage:
    >>> from crossref_local import cache
    >>> from crossref_local.cache_viz import plot_year_citations, plot_citation_network
    >>> # Scatter plot: year vs citations
    >>> plot_year_citations("epilepsy", output="epilepsy_scatter.png")
    >>> # Citation network
    >>> plot_citation_network("epilepsy", output="epilepsy_network.html")
"""

from typing import Any, Dict, List, Optional, Tuple

from . import cache


def plot_year_citations(
    cache_name: str,
    output: Optional[str] = None,
    top_n: int = 10,
    highlight_threshold: Optional[int] = None,
    figsize: Tuple[int, int] = (10, 6),
) -> Dict[str, Any]:
    """Plot year vs citation count scatter plot.

    Helps identify highly cited papers across publication years.

    Args:
        cache_name: Name of cache to analyze
        output: Output file path (png/pdf/svg). None for interactive display.
        top_n: Number of top-cited papers to label
        highlight_threshold: Citation threshold to highlight (draws horizontal line)
        figsize: Figure size in inches

    Returns:
        Dict with plot path and top papers list

    Example:
        >>> plot_year_citations("epilepsy", output="scatter.png", top_n=5)
    """
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib required. Install with: pip install matplotlib")

    papers = cache.load(cache_name)

    # Extract year and citations
    data = []
    for p in papers:
        year = p.get("year")
        citations = p.get("citation_count", 0)
        if year and citations is not None:
            data.append(
                {
                    "doi": p.get("doi"),
                    "title": p.get("title", "")[:50],
                    "year": year,
                    "citations": citations,
                    "journal": p.get("journal", ""),
                }
            )

    if not data:
        return {"error": "No papers with year and citation data"}

    # Sort by citations for top-N
    data_sorted = sorted(data, key=lambda x: -x["citations"])
    top_papers = data_sorted[:top_n]

    # Create scatter plot
    fig, ax = plt.subplots(figsize=figsize)

    years = [d["year"] for d in data]
    citations = [d["citations"] for d in data]

    ax.scatter(years, citations, alpha=0.5, s=20)

    # Highlight top papers
    for p in top_papers:
        ax.annotate(
            p["title"][:30] + "...",
            (p["year"], p["citations"]),
            fontsize=7,
            alpha=0.8,
            xytext=(5, 5),
            textcoords="offset points",
        )

    # Threshold line
    if highlight_threshold:
        ax.axhline(y=highlight_threshold, color="r", linestyle="--", alpha=0.5)

    ax.set_xlabel("Publication Year")
    ax.set_ylabel("Citation Count")
    ax.set_title(f"Year vs Citations: {cache_name}")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output:
        plt.savefig(output, dpi=150)
        plt.close()
        result_path = output
    else:
        plt.show()
        result_path = None

    return {
        "output": result_path,
        "total_papers": len(data),
        "top_papers": [
            {
                "doi": p["doi"],
                "title": p["title"],
                "year": p["year"],
                "citations": p["citations"],
            }
            for p in top_papers
        ],
    }


def plot_citation_network(
    cache_name: str,
    output: Optional[str] = None,
    max_nodes: int = 100,
    include_external: bool = False,
) -> Dict[str, Any]:
    """Generate citation network visualization.

    Creates an interactive HTML network graph showing citation relationships
    between papers in the cache.

    Args:
        cache_name: Name of cache to analyze
        output: Output HTML file path. None returns network data.
        max_nodes: Maximum papers to include (sorted by citations)
        include_external: Include referenced papers not in cache

    Returns:
        Dict with network stats and output path

    Example:
        >>> plot_citation_network("epilepsy", output="network.html", max_nodes=50)
    """
    try:
        from pyvis.network import Network
    except ImportError:
        raise ImportError("pyvis required. Install with: pip install pyvis")

    papers = cache.load(cache_name)

    # Build DOI lookup
    doi_to_paper = {p["doi"]: p for p in papers if p.get("doi")}

    # Sort by citations and take top N
    papers_sorted = sorted(papers, key=lambda x: -(x.get("citation_count") or 0))
    selected = papers_sorted[:max_nodes]
    selected_dois = {p["doi"] for p in selected if p.get("doi")}

    # Create network
    net = Network(height="750px", width="100%", bgcolor="#ffffff", font_color="black")
    net.barnes_hut()

    # Add nodes
    for p in selected:
        doi = p.get("doi")
        if not doi:
            continue

        title = p.get("title", "No title")[:40]
        citations = p.get("citation_count", 0)
        year = p.get("year", "?")

        # Size by citations (log scale)
        size = 10 + min(citations, 500) ** 0.5 * 2

        net.add_node(
            doi,
            label=f"{title}...\n({year})",
            title=f"{p.get('title', 'No title')}\n{doi}\nCitations: {citations}",
            size=size,
            color="#3498db" if citations > 50 else "#95a5a6",
        )

    # Add edges from references
    edge_count = 0
    for p in selected:
        doi = p.get("doi")
        refs = p.get("references", [])
        if not doi or not refs:
            continue

        for ref in refs:
            if ref in selected_dois:
                # Both papers in cache
                net.add_edge(doi, ref)
                edge_count += 1
            elif include_external and ref not in selected_dois:
                # External reference
                if ref not in [n["id"] for n in net.nodes]:
                    net.add_node(
                        ref,
                        label=ref[:20],
                        title=f"External: {ref}",
                        size=5,
                        color="#e74c3c",
                    )
                net.add_edge(doi, ref)
                edge_count += 1

    result = {
        "nodes": len(net.nodes),
        "edges": edge_count,
        "cache_papers": len(papers),
        "selected_papers": len(selected),
    }

    if output:
        net.save_graph(output)
        result["output"] = output
    else:
        result["network_data"] = {
            "nodes": [{"id": n["id"], "label": n["label"]} for n in net.nodes],
            "edges": edge_count,
        }

    return result


def get_top_cited(
    cache_name: str,
    n: int = 20,
    year_min: Optional[int] = None,
    year_max: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Get top cited papers from cache.

    Args:
        cache_name: Name of cache
        n: Number of papers to return
        year_min: Filter by minimum year
        year_max: Filter by maximum year

    Returns:
        List of paper dicts sorted by citation count
    """
    papers = cache.query(
        cache_name,
        include_citations=True,
        year_min=year_min,
        year_max=year_max,
    )

    # Sort by citations
    papers_sorted = sorted(papers, key=lambda x: -(x.get("citation_count") or 0))
    return papers_sorted[:n]


def get_citation_summary(cache_name: str) -> Dict[str, Any]:
    """Get citation statistics summary.

    Args:
        cache_name: Name of cache

    Returns:
        Dict with citation statistics
    """
    papers = cache.load(cache_name)

    citations = [
        p.get("citation_count", 0)
        for p in papers
        if p.get("citation_count") is not None
    ]

    if not citations:
        return {"error": "No citation data available"}

    import statistics

    return {
        "total_papers": len(papers),
        "papers_with_citations": len(citations),
        "total_citations": sum(citations),
        "mean": round(statistics.mean(citations), 2),
        "median": statistics.median(citations),
        "stdev": round(statistics.stdev(citations), 2) if len(citations) > 1 else 0,
        "max": max(citations),
        "min": min(citations),
        "highly_cited_50": sum(1 for c in citations if c >= 50),
        "highly_cited_100": sum(1 for c in citations if c >= 100),
    }
