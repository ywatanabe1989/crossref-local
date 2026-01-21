"""MCP server management commands for crossref-local CLI."""

import json
import sys

import click

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group("mcp", context_settings=CONTEXT_SETTINGS)
def mcp():
    """MCP (Model Context Protocol) server management.

    \b
    Commands for running and managing the MCP server that enables
    AI assistants like Claude to search academic papers.

    \b
    Quick start:
      crossref-local mcp start              # Start stdio server
      crossref-local mcp start -t http      # Start HTTP server
      crossref-local mcp doctor             # Check dependencies
      crossref-local mcp installation       # Show config snippets
    """
    pass


@mcp.command("start", context_settings=CONTEXT_SETTINGS)
@click.option(
    "-t",
    "--transport",
    type=click.Choice(["stdio", "sse", "http"]),
    default="stdio",
    help="Transport protocol (http recommended for remote)",
)
@click.option(
    "--host",
    default="localhost",
    envvar="CROSSREF_LOCAL_MCP_HOST",
    help="Host for HTTP/SSE transport",
)
@click.option(
    "--port",
    default=8082,
    type=int,
    envvar="CROSSREF_LOCAL_MCP_PORT",
    help="Port for HTTP/SSE transport",
)
def start_cmd(transport: str, host: str, port: int):
    """Start the MCP server.

    \b
    Transports:
      stdio  - Standard I/O (default, for Claude Desktop local)
      http   - Streamable HTTP (recommended for remote/persistent)
      sse    - Server-Sent Events (deprecated as of MCP spec 2025-03-26)

    \b
    Examples:
      crossref-local mcp start                    # stdio for Claude Desktop
      crossref-local mcp start -t http            # HTTP on localhost:8082
      crossref-local mcp start -t http --port 9000  # Custom port
    """
    try:
        from .mcp_server import run_server
    except ImportError:
        click.echo(
            "MCP server requires fastmcp. Install with:\n"
            "  pip install crossref-local[mcp]",
            err=True,
        )
        sys.exit(1)

    run_server(transport=transport, host=host, port=port)


@mcp.command("doctor", context_settings=CONTEXT_SETTINGS)
def doctor_cmd():
    """Check MCP server dependencies and configuration.

    Verifies that all required packages are installed and
    the database is accessible.
    """
    click.echo("MCP Server Health Check")
    click.echo("=" * 40)

    issues = []

    # Check fastmcp
    try:
        import fastmcp

        click.echo(f"[OK] fastmcp {fastmcp.__version__}")
    except ImportError:
        click.echo("[FAIL] fastmcp not installed")
        issues.append("Install fastmcp: pip install crossref-local[mcp]")

    # Check database
    try:
        from . import info

        db_info = info()
        works = db_info.get("works", 0)
        click.echo(f"[OK] Database: {works:,} works")
    except Exception as e:
        click.echo(f"[FAIL] Database: {e}")
        issues.append("Configure database: export CROSSREF_LOCAL_DB=/path/to/db")

    # Check FTS index
    try:
        from . import info

        db_info = info()
        fts = db_info.get("fts_indexed", 0)
        if fts > 0:
            click.echo(f"[OK] FTS index: {fts:,} indexed")
        else:
            click.echo("[WARN] FTS index: not built")
            issues.append("Build FTS index: make fts-build")
    except Exception:
        pass

    click.echo()
    if issues:
        click.echo("Issues found:")
        for issue in issues:
            click.echo(f"  - {issue}")
        sys.exit(1)
    else:
        click.echo("All checks passed!")


@mcp.command("installation", context_settings=CONTEXT_SETTINGS)
@click.option(
    "-t",
    "--transport",
    type=click.Choice(["stdio", "http"]),
    default="stdio",
    help="Transport type for config",
)
@click.option("--host", default="localhost", help="Host for HTTP transport")
@click.option("--port", default=8082, type=int, help="Port for HTTP transport")
def installation_cmd(transport: str, host: str, port: int):
    """Show MCP client configuration snippets.

    Outputs JSON configuration for Claude Desktop or other MCP clients.

    \b
    Examples:
      crossref-local mcp installation              # stdio config
      crossref-local mcp installation -t http      # HTTP config
    """
    if transport == "stdio":
        config = {
            "mcpServers": {
                "crossref-local": {
                    "command": "crossref-local",
                    "args": ["mcp", "start"],
                }
            }
        }
        click.echo("Claude Desktop configuration (stdio):")
        click.echo()
        click.echo(
            "Add to ~/Library/Application Support/Claude/claude_desktop_config.json"
        )
        click.echo("or ~/.config/claude/claude_desktop_config.json:")
        click.echo()
    else:
        url = f"http://{host}:{port}/mcp"
        config = {"mcpServers": {"crossref-local": {"url": url}}}
        click.echo(f"Claude Desktop configuration (HTTP at {url}):")
        click.echo()
        click.echo("First start the server:")
        click.echo(f"  crossref-local mcp start -t http --host {host} --port {port}")
        click.echo()
        click.echo("Then add to claude_desktop_config.json:")
        click.echo()

    click.echo(json.dumps(config, indent=2))


@mcp.command("list-tools", context_settings=CONTEXT_SETTINGS)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_tools_cmd(as_json: bool):
    """List available MCP tools.

    Shows all tools exposed by the MCP server with their descriptions.
    """
    tools = [
        {
            "name": "search",
            "description": "Search for academic works by title, abstract, or authors",
            "parameters": ["query", "limit", "offset", "with_abstracts"],
        },
        {
            "name": "search_by_doi",
            "description": "Get detailed information about a work by DOI",
            "parameters": ["doi", "as_citation"],
        },
        {
            "name": "status",
            "description": "Get database statistics and status",
            "parameters": [],
        },
        {
            "name": "enrich_dois",
            "description": "Enrich DOIs with full metadata including citations",
            "parameters": ["dois"],
        },
        {
            "name": "cache_create",
            "description": "Create a paper cache from search query",
            "parameters": ["name", "query", "limit"],
        },
        {
            "name": "cache_query",
            "description": "Query cached papers with field filtering",
            "parameters": ["name", "fields", "year_min", "year_max", "limit"],
        },
        {
            "name": "cache_stats",
            "description": "Get cache statistics",
            "parameters": ["name"],
        },
        {
            "name": "cache_list",
            "description": "List all available caches",
            "parameters": [],
        },
        {
            "name": "cache_top_cited",
            "description": "Get top cited papers from cache",
            "parameters": ["name", "n", "year_min", "year_max"],
        },
        {
            "name": "cache_citation_summary",
            "description": "Get citation statistics for cached papers",
            "parameters": ["name"],
        },
        {
            "name": "cache_plot_scatter",
            "description": "Generate year vs citations scatter plot",
            "parameters": ["name", "output", "top_n"],
        },
        {
            "name": "cache_plot_network",
            "description": "Generate citation network visualization",
            "parameters": ["name", "output", "max_nodes"],
        },
        {
            "name": "cache_export",
            "description": "Export cache to file (json, csv, bibtex, dois)",
            "parameters": ["name", "output_path", "format", "fields"],
        },
    ]

    if as_json:
        click.echo(json.dumps(tools, indent=2))
    else:
        click.echo("CrossRef Local MCP Tools")
        click.echo("=" * 50)
        click.echo()
        for tool in tools:
            click.echo(f"  {tool['name']}")
            click.echo(f"    {tool['description']}")
            if tool["parameters"]:
                click.echo(f"    Parameters: {', '.join(tool['parameters'])}")
            click.echo()


def register_mcp_commands(cli_group):
    """Register MCP commands with the main CLI group."""
    cli_group.add_command(mcp)
