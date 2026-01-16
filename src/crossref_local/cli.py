"""Command-line interface for crossref_local."""

import click
import json
import re
import sys
from typing import Optional

from rich.console import Console

from . import search, get, info, __version__

console = Console()


def _strip_xml_tags(text: str) -> str:
    """Strip XML/JATS tags from abstract text."""
    if not text:
        return text
    # Remove XML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


class AliasedGroup(click.Group):
    """Click group that supports command aliases."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._aliases = {}

    def command(self, *args, aliases=None, **kwargs):
        """Decorator that registers aliases for commands."""

        def decorator(f):
            cmd = super(AliasedGroup, self).command(*args, **kwargs)(f)
            if aliases:
                for alias in aliases:
                    self._aliases[alias] = cmd.name
            return cmd

        return decorator

    def get_command(self, ctx, cmd_name):
        """Resolve aliases to actual commands."""
        cmd_name = self._aliases.get(cmd_name, cmd_name)
        return super().get_command(ctx, cmd_name)

    def format_commands(self, ctx, formatter):
        """Format commands with aliases shown inline."""
        commands = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            if cmd is None or cmd.hidden:
                continue

            # Find aliases for this command
            aliases = [a for a, c in self._aliases.items() if c == subcommand]
            if aliases:
                name = f"{subcommand} ({', '.join(aliases)})"
            else:
                name = subcommand

            help_text = cmd.get_short_help_str(limit=50)
            commands.append((name, help_text))

        if commands:
            with formatter.section("Commands"):
                formatter.write_dl(commands)


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def _print_recursive_help(ctx, param, value):
    """Callback for --help-recursive flag."""
    if not value or ctx.resilient_parsing:
        return

    def _print_command_help(cmd, prefix: str, parent_ctx):
        """Recursively print help for a command and its subcommands."""
        console.print(f"\n[bold cyan]━━━ {prefix} ━━━[/bold cyan]")
        sub_ctx = click.Context(cmd, info_name=prefix.split()[-1], parent=parent_ctx)
        console.print(cmd.get_help(sub_ctx))

        if isinstance(cmd, click.Group):
            for sub_name, sub_cmd in sorted(cmd.commands.items()):
                _print_command_help(sub_cmd, f"{prefix} {sub_name}", sub_ctx)

    # Print main help
    console.print("[bold cyan]━━━ crossref-local ━━━[/bold cyan]")
    console.print(ctx.get_help())

    # Print all subcommands recursively
    for name, cmd in sorted(cli.commands.items()):
        _print_command_help(cmd, f"crossref-local {name}", ctx)

    ctx.exit(0)


@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name="crossref-local")
@click.option("--http", is_flag=True, help="Use HTTP API instead of direct database")
@click.option(
    "--api-url",
    envvar="CROSSREF_LOCAL_API_URL",
    help="API URL for http mode (default: auto-detect)",
)
@click.option(
    "--help-recursive",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_print_recursive_help,
    help="Show help for all commands recursively.",
)
@click.pass_context
def cli(ctx, http: bool, api_url: str):
    """Local CrossRef database with 167M+ works and full-text search.

    Supports both direct database access (db mode) and HTTP API (http mode).

    \b
    DB mode (default if database found):
      crossref-local search "machine learning"

    \b
    HTTP mode (connect to API server):
      crossref-local --http search "machine learning"
    """
    from .config import Config

    ctx.ensure_object(dict)

    if api_url:
        Config.set_api_url(api_url)
    elif http:
        Config.set_mode("http")


def _get_if_fast(db, issn: str, cache: dict) -> Optional[float]:
    """Fast IF lookup from pre-computed OpenAlex data."""
    if issn in cache:
        return cache[issn]
    row = db.fetchone(
        "SELECT two_year_mean_citedness FROM journals_openalex WHERE issns LIKE ?",
        (f"%{issn}%",),
    )
    cache[issn] = row["two_year_mean_citedness"] if row else None
    return cache[issn]


@cli.command("search", context_settings=CONTEXT_SETTINGS)
@click.argument("query")
@click.option(
    "-n", "--number", "limit", default=10, show_default=True, help="Number of results"
)
@click.option("-o", "--offset", default=0, help="Skip first N results")
@click.option("-a", "--abstracts", is_flag=True, help="Show abstracts")
@click.option("-A", "--authors", is_flag=True, help="Show authors")
@click.option(
    "-if", "--impact-factor", "with_if", is_flag=True, help="Show journal impact factor"
)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search_cmd(
    query: str,
    limit: int,
    offset: int,
    abstracts: bool,
    authors: bool,
    with_if: bool,
    as_json: bool,
):
    """Search for works by title, abstract, or authors."""
    from .db import get_db

    try:
        results = search(query, limit=limit, offset=offset)
    except ConnectionError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("\nRun 'crossref-local status' to check configuration.", err=True)
        sys.exit(1)

    # Cache for fast IF lookups
    if_cache = {}
    db = get_db() if with_if else None

    if as_json:
        output = {
            "query": results.query,
            "total": results.total,
            "elapsed_ms": results.elapsed_ms,
            "works": [w.to_dict() for w in results.works],
        }
        click.echo(json.dumps(output, indent=2))
    else:
        click.echo(f"Found {results.total:,} matches in {results.elapsed_ms:.1f}ms\n")
        for i, work in enumerate(results.works, start=offset + 1):
            title = _strip_xml_tags(work.title) if work.title else "Untitled"
            year = f"({work.year})" if work.year else ""
            click.echo(f"{i}. {title} {year}")
            click.echo(f"   DOI: {work.doi}")
            if authors and work.authors:
                authors_str = ", ".join(work.authors[:5])
                if len(work.authors) > 5:
                    authors_str += f" et al. ({len(work.authors)} total)"
                click.echo(f"   Authors: {authors_str}")
            if work.journal:
                journal_line = f"   Journal: {work.journal}"
                # Fast IF lookup from pre-computed table
                if with_if and work.issn:
                    impact_factor = _get_if_fast(db, work.issn, if_cache)
                    if impact_factor is not None:
                        journal_line += f" (IF: {impact_factor:.2f}, OpenAlex)"
                click.echo(journal_line)
            if abstracts and work.abstract:
                # Strip XML tags and truncate
                abstract = _strip_xml_tags(work.abstract)
                if len(abstract) > 500:
                    abstract = abstract[:500] + "..."
                click.echo(f"   Abstract: {abstract}")
            click.echo()


@cli.command("search-by-doi", context_settings=CONTEXT_SETTINGS)
@click.argument("doi")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--citation", is_flag=True, help="Output as citation")
def search_by_doi_cmd(doi: str, as_json: bool, citation: bool):
    """Search for a work by DOI."""
    try:
        work = get(doi)
    except ConnectionError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("\nRun 'crossref-local status' to check configuration.", err=True)
        sys.exit(1)

    if work is None:
        click.echo(f"DOI not found: {doi}", err=True)
        sys.exit(1)

    if as_json:
        click.echo(json.dumps(work.to_dict(), indent=2))
    elif citation:
        click.echo(work.citation())
    else:
        click.echo(f"Title: {work.title}")
        click.echo(f"Authors: {', '.join(work.authors)}")
        click.echo(f"Year: {work.year}")
        click.echo(f"Journal: {work.journal}")
        click.echo(f"DOI: {work.doi}")
        if work.citation_count:
            click.echo(f"Citations: {work.citation_count}")


@cli.command(context_settings=CONTEXT_SETTINGS)
def status():
    """Show status and configuration."""
    from .config import DEFAULT_DB_PATHS, DEFAULT_API_URLS
    import os

    click.echo("CrossRef Local - Status")
    click.echo("=" * 50)
    click.echo()

    # Check environment variables
    click.echo("Environment Variables:")
    click.echo()

    env_vars = [
        (
            "CROSSREF_LOCAL_DB",
            "Path to SQLite database file",
            os.environ.get("CROSSREF_LOCAL_DB"),
        ),
        (
            "CROSSREF_LOCAL_API_URL",
            "HTTP API URL (e.g., http://localhost:8333)",
            os.environ.get("CROSSREF_LOCAL_API_URL"),
        ),
        (
            "CROSSREF_LOCAL_MODE",
            "Force mode: 'db', 'http', or 'auto'",
            os.environ.get("CROSSREF_LOCAL_MODE"),
        ),
        (
            "CROSSREF_LOCAL_HOST",
            "Host for run-server-http (default: 0.0.0.0)",
            os.environ.get("CROSSREF_LOCAL_HOST"),
        ),
        (
            "CROSSREF_LOCAL_PORT",
            "Port for run-server-http (default: 8333)",
            os.environ.get("CROSSREF_LOCAL_PORT"),
        ),
    ]

    for var_name, description, value in env_vars:
        if value:
            if var_name == "CROSSREF_LOCAL_DB":
                status = " (OK)" if os.path.exists(value) else " (NOT FOUND)"
            else:
                status = ""
            click.echo(f"  {var_name}={value}{status}")
            click.echo(f"      | {description}")
        else:
            click.echo(f"  {var_name} (not set)")
            click.echo(f"      | {description}")
        click.echo()

    click.echo()

    # Check default database paths
    click.echo("Local Database Locations:")
    db_found = None
    for path in DEFAULT_DB_PATHS:
        if path.exists():
            click.echo(f"  [OK] {path}")
            if db_found is None:
                db_found = path
        else:
            click.echo(f"  [ ] {path}")

    click.echo()

    # Check API servers
    click.echo("API Servers:")
    api_found = None
    api_compatible = False
    for url in DEFAULT_API_URLS:
        try:
            import urllib.request
            import json as json_module

            # Check root endpoint for version
            req = urllib.request.Request(f"{url}/", method="GET")
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    data = json_module.loads(resp.read().decode())
                    server_version = data.get("version", "unknown")

                    # Check version compatibility
                    if server_version == __version__:
                        click.echo(f"  [OK] {url} (v{server_version})")
                        api_compatible = True
                    else:
                        click.echo(
                            f"  [WARN] {url} (v{server_version} != v{__version__})"
                        )
                        click.echo(
                            f"         Server version mismatch - may be incompatible"
                        )

                    if api_found is None:
                        api_found = url
                else:
                    click.echo(f"  [ ] {url}")
        except Exception:
            click.echo(f"  [ ] {url}")

    click.echo()

    # Summary and recommendations
    if db_found:
        click.echo(f"Local database: {db_found}")
        try:
            db_info = info()
            click.echo(f"  Works: {db_info.get('works', 0):,}")
            click.echo(f"  FTS indexed: {db_info.get('fts_indexed', 0):,}")
        except Exception as e:
            click.echo(f"  Error: {e}", err=True)
        click.echo()
        click.echo("Ready! Try:")
        click.echo('  crossref-local search "machine learning"')
    elif api_found:
        click.echo(f"HTTP API available: {api_found}")
        click.echo()
        click.echo("Ready! Try:")
        click.echo('  crossref-local --http search "machine learning"')
        click.echo()
        click.echo("Or set environment:")
        click.echo("  export CROSSREF_LOCAL_MODE=http")
    else:
        click.echo("No database or API server found!")
        click.echo()
        click.echo("Options:")
        click.echo("  1. Direct database access (db mode):")
        click.echo("     export CROSSREF_LOCAL_DB=/path/to/crossref.db")
        click.echo()
        click.echo("  2. HTTP API (connect to server):")
        click.echo("     crossref-local --http search 'query'")


@cli.command("run-server-mcp", context_settings=CONTEXT_SETTINGS)
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
def serve_mcp(transport: str, host: str, port: int):
    """Run MCP (Model Context Protocol) server.

    \b
    Transports:
      stdio  - Standard I/O (default, for Claude Desktop local)
      http   - Streamable HTTP (recommended for remote/persistent)
      sse    - Server-Sent Events (deprecated as of MCP spec 2025-03-26)

    \b
    Local configuration (stdio):
      {
        "mcpServers": {
          "crossref": {
            "command": "crossref-local",
            "args": ["run-server-mcp"]
          }
        }
      }

    \b
    Remote configuration (http):
      # Start server:
      crossref-local run-server-mcp -t http --host 0.0.0.0 --port 8082

      # Client config:
      {
        "mcpServers": {
          "crossref-remote": {
            "url": "http://your-server:8082/mcp"
          }
        }
      }

    \b
    See docs/remote-deployment.md for systemd and Docker setup.
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


@cli.command("run-server-http", context_settings=CONTEXT_SETTINGS)
@click.option(
    "--host", default="0.0.0.0", envvar="CROSSREF_LOCAL_HOST", help="Host to bind"
)
@click.option(
    "--port",
    default=8333,
    type=int,
    envvar="CROSSREF_LOCAL_PORT",
    help="Port to listen on",
)
def serve_http(host: str, port: int):
    """Run HTTP API server.

    \b
    This runs a FastAPI server that provides proper full-text search
    using FTS5 index across all 167M+ papers.

    \b
    Example:
      crossref-local run-server-http                  # Run on 0.0.0.0:8333
      crossref-local run-server-http --port 8080      # Custom port

    \b
    Then connect with http mode:
      crossref-local --http search "CRISPR"
      curl "http://localhost:8333/works?q=CRISPR&limit=10"
    """
    try:
        from .server import run_server
    except ImportError:
        click.echo(
            "API server requires fastapi and uvicorn. Install with:\n"
            "  pip install fastapi uvicorn",
            err=True,
        )
        sys.exit(1)

    click.echo(f"Starting CrossRef Local API server on {host}:{port}")
    click.echo(f"Search endpoint: http://{host}:{port}/search?q=<query>")
    click.echo(f"Docs: http://{host}:{port}/docs")
    run_server(host=host, port=port)


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
