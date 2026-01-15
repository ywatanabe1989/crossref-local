"""MCP server for CrossRef Local - Claude integration.

This server exposes crossref-local functionality as MCP tools,
enabling Claude Desktop and other MCP clients to search academic papers.

Usage:
    crossref-local serve                    # stdio (Claude Desktop)
    crossref-local serve -t http --port 8082  # HTTP transport
    crossref-local-mcp                      # Direct entry point
"""

import json
from typing import Optional

from fastmcp import FastMCP

from . import search as _search, get as _get, info as _info, __version__

# Initialize MCP server
mcp = FastMCP(
    name="crossref-local",
    instructions="Local CrossRef database with 167M+ works and full-text search. "
    "Use search to find papers, search_by_doi for DOI lookup, and status for stats.",
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
