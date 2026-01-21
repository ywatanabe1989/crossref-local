"""MCP server for CrossRef Local - Claude integration.

This server exposes crossref-local functionality as MCP tools,
enabling Claude Desktop and other MCP clients to search academic papers.

Usage:
    crossref-local serve                    # stdio (Claude Desktop)
    crossref-local serve -t http --port 8082  # HTTP transport
    crossref-local-mcp                      # Direct entry point
"""

import json

from fastmcp import FastMCP


from . import (
    get as _get,
    info as _info,
    search as _search,
)

# Initialize MCP server
mcp = FastMCP(
    name="crossref-local",
    instructions="Local CrossRef database with 167M+ works and full-text search. "
    "Use search to find papers, search_by_doi for DOI lookup, enrich_dois to add "
    "citation counts and references, and status for stats.",
)


@mcp.tool()
def search(
    query: str,
    limit: int = 10,
    offset: int = 0,
    with_abstracts: bool = False,
) -> str:
    """Search for academic works by title, abstract, or authors.

    Uses FTS5 full-text search index for fast searching across 167M+ papers.
    Supports FTS5 query syntax: AND, OR, NOT, "exact phrases".

    Args:
        query: Search query (e.g., "machine learning", "CRISPR", "neural network AND hippocampus")
        limit: Maximum number of results to return (default: 10, max: 100)
        offset: Skip first N results for pagination (default: 0)
        with_abstracts: Include abstracts in results (default: False)

    Returns:
        JSON string with search results including total count and matching works.

    Examples:
        search("machine learning")
        search("CRISPR", limit=20)
        search("neural network AND memory", with_abstracts=True)
    """
    results = _search(query, limit=min(limit, 100), offset=offset)

    works_data = []
    for work in results.works:
        work_dict = {
            "doi": work.doi,
            "title": work.title,
            "authors": work.authors,
            "year": work.year,
            "journal": work.journal,
        }
        if with_abstracts and work.abstract:
            work_dict["abstract"] = work.abstract
        works_data.append(work_dict)

    return json.dumps(
        {
            "query": results.query,
            "total": results.total,
            "returned": len(works_data),
            "elapsed_ms": round(results.elapsed_ms, 2),
            "works": works_data,
        },
        indent=2,
    )


@mcp.tool()
def search_by_doi(doi: str, as_citation: bool = False) -> str:
    """Get detailed information about a work by DOI.

    Args:
        doi: Digital Object Identifier (e.g., "10.1038/nature12373")
        as_citation: Return formatted citation instead of full metadata

    Returns:
        JSON string with work metadata, or formatted citation string.

    Examples:
        search_by_doi("10.1038/nature12373")
        search_by_doi("10.1126/science.aax0758", as_citation=True)
    """
    work = _get(doi)

    if work is None:
        return json.dumps({"error": f"DOI not found: {doi}"})

    if as_citation:
        return work.citation()

    return json.dumps(work.to_dict(), indent=2)


@mcp.tool()
def status() -> str:
    """Get database statistics and status.

    Returns:
        JSON string with database path, work count, FTS index count, and citation count.
    """
    db_info = _info()
    return json.dumps(db_info, indent=2)


@mcp.tool()
def enrich_dois(dois: list[str]) -> str:
    """Enrich DOIs with full metadata including citation counts and references.

    Use this after search() to get detailed metadata for papers.
    The search() tool returns basic info (title, authors, year, journal).
    This tool adds: citation_count, references, volume, issue, publisher, etc.

    Typical workflow:
    1. search("epilepsy seizure prediction") -> get DOIs
    2. enrich_dois([doi1, doi2, ...]) -> get full metadata

    Args:
        dois: List of DOIs to enrich (e.g., ["10.1038/nature12373", "10.1126/science.aax0758"])

    Returns:
        JSON string with enriched works including citation_count and references.

    Examples:
        enrich_dois(["10.1038/nature12373"])
        enrich_dois(["10.1038/s41467-017-02577-y", "10.1093/brain/aww019"])
    """
    from . import get_many as _get_many

    works = _get_many(dois)

    works_data = []
    for work in works:
        works_data.append(work.to_dict())

    return json.dumps(
        {
            "requested": len(dois),
            "found": len(works_data),
            "works": works_data,
        },
        indent=2,
    )


@mcp.tool()
def cache_create(
    name: str,
    query: str,
    limit: int = 1000,
) -> str:
    """Create a paper cache from search query.

    Fetches full metadata for papers matching query and saves to disk cache.
    Use this to build a reusable paper collection for a research topic.

    Args:
        name: Cache name (e.g., "epilepsy", "alzheimers")
        query: FTS search query
        limit: Max papers to cache (default: 1000)

    Returns:
        JSON with cache info (path, paper count, size)

    Example:
        cache_create("epilepsy", "epilepsy seizure prediction", limit=500)
    """
    from . import cache

    info = cache.create(name, query=query, limit=limit)
    return json.dumps(info.to_dict(), indent=2)


@mcp.tool()
def cache_query(
    name: str,
    fields: list[str] | None = None,
    include_abstract: bool = False,
    include_references: bool = False,
    include_citations: bool = False,
    year_min: int | None = None,
    year_max: int | None = None,
    journal: str | None = None,
    limit: int | None = None,
) -> str:
    """Query cached papers with field filtering.

    Returns minimal data to reduce context usage. Specify only fields needed.

    Args:
        name: Cache name
        fields: Explicit field list (e.g., ["doi", "title", "year"])
        include_abstract: Include abstract (default: False)
        include_references: Include references list (default: False)
        include_citations: Include citation_count (default: False)
        year_min: Filter by minimum year
        year_max: Filter by maximum year
        journal: Filter by journal name (substring match)
        limit: Max results to return

    Returns:
        JSON array of filtered papers

    Examples:
        cache_query("epilepsy", fields=["doi", "title", "year"])
        cache_query("epilepsy", year_min=2020, include_citations=True, limit=50)
    """
    from . import cache

    papers = cache.query(
        name,
        fields=fields,
        include_abstract=include_abstract,
        include_references=include_references,
        include_citations=include_citations,
        year_min=year_min,
        year_max=year_max,
        journal=journal,
        limit=limit,
    )
    return json.dumps({"count": len(papers), "papers": papers}, indent=2)


@mcp.tool()
def cache_stats(name: str) -> str:
    """Get cache statistics.

    Returns year distribution, top journals, citation stats without loading full data.

    Args:
        name: Cache name

    Returns:
        JSON with statistics (paper_count, year_range, top_journals, etc.)
    """
    from . import cache

    stats = cache.stats(name)
    return json.dumps(stats, indent=2)


@mcp.tool()
def cache_list() -> str:
    """List all available caches.

    Returns:
        JSON array of cache info (name, path, paper_count, size)
    """
    from . import cache

    caches = cache.list_caches()
    return json.dumps([c.to_dict() for c in caches], indent=2)


@mcp.tool()
def cache_top_cited(
    name: str,
    n: int = 20,
    year_min: int | None = None,
    year_max: int | None = None,
) -> str:
    """Get top cited papers from cache.

    Args:
        name: Cache name
        n: Number of papers to return
        year_min: Filter by minimum year
        year_max: Filter by maximum year

    Returns:
        JSON array of top cited papers
    """
    from .cache_viz import get_top_cited

    papers = get_top_cited(name, n=n, year_min=year_min, year_max=year_max)
    return json.dumps(papers, indent=2)


@mcp.tool()
def cache_citation_summary(name: str) -> str:
    """Get citation statistics for cached papers.

    Returns mean, median, max citations and counts of highly cited papers.

    Args:
        name: Cache name

    Returns:
        JSON with citation statistics
    """
    from .cache_viz import get_citation_summary

    summary = get_citation_summary(name)
    return json.dumps(summary, indent=2)


@mcp.tool()
def cache_plot_scatter(
    name: str,
    output: str,
    top_n: int = 10,
) -> str:
    """Generate year vs citations scatter plot.

    Saves plot to file and returns top cited papers.

    Args:
        name: Cache name
        output: Output file path (png/pdf/svg)
        top_n: Number of top papers to label on plot

    Returns:
        JSON with output path and top papers list
    """
    from .cache_viz import plot_year_citations

    result = plot_year_citations(name, output=output, top_n=top_n)
    return json.dumps(result, indent=2)


@mcp.tool()
def cache_plot_network(
    name: str,
    output: str,
    max_nodes: int = 100,
) -> str:
    """Generate citation network visualization.

    Creates interactive HTML graph showing citation relationships.

    Args:
        name: Cache name
        output: Output HTML file path
        max_nodes: Maximum papers to include

    Returns:
        JSON with network stats
    """
    from .cache_viz import plot_citation_network

    result = plot_citation_network(name, output=output, max_nodes=max_nodes)
    return json.dumps(result, indent=2)


@mcp.tool()
def cache_export(
    name: str,
    output_path: str,
    format: str = "json",
    fields: list[str] | None = None,
) -> str:
    """Export cache to file.

    Args:
        name: Cache name
        output_path: Output file path
        format: Export format (json, csv, bibtex, dois)
        fields: Fields to include (for json/csv)

    Returns:
        JSON with output path
    """
    from . import cache

    path = cache.export(name, output_path, format=format, fields=fields)
    return json.dumps({"exported": path, "format": format})


def run_server(
    transport: str = "stdio",
    host: str = "localhost",
    port: int = 8082,
) -> None:
    """Run the MCP server.

    Args:
        transport: Transport protocol ("stdio", "sse", or "http")
        host: Host for HTTP/SSE transport
        port: Port for HTTP/SSE transport
    """
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "sse":
        mcp.run(transport="sse", host=host, port=port)
    elif transport == "http":
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        raise ValueError(f"Unknown transport: {transport}")


def main():
    """Entry point for crossref-local-mcp command."""
    run_server(transport="stdio")


if __name__ == "__main__":
    main()
