"""Command-line interface for crossref_local."""

import click
import json
import logging
import re
import sys
from typing import Optional

from . import search, get, count, info, __version__

from .impact_factor import ImpactFactorCalculator

# Suppress noisy warnings from impact_factor module in CLI
logging.getLogger("crossref_local.impact_factor").setLevel(logging.ERROR)


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


@click.group(cls=AliasedGroup, context_settings=CONTEXT_SETTINGS)
@click.version_option(version=__version__, prog_name="crossref-local")
@click.option(
    "--remote", "-r", is_flag=True, help="Use remote API instead of local database"
)
@click.option(
    "--api-url",
    envvar="CROSSREF_LOCAL_API",
    help="API URL for remote mode (default: auto-detect)",
)
@click.pass_context
def cli(ctx, remote: bool, api_url: str):
    """Local CrossRef database with 167M+ works and full-text search.

    Supports both local database access and remote API mode.

    \b
    Local mode (default if database found):
      crossref-local search "machine learning"

    \b
    Remote mode (via SSH tunnel):
      ssh -L 3333:127.0.0.1:3333 nas  # First, create tunnel
      crossref-local --remote search "machine learning"
    """
    from .config import Config

    ctx.ensure_object(dict)

    if api_url:
        Config.set_api_url(api_url)
    elif remote:
        Config.set_mode("remote")


def _get_if_fast(db, issn: str, cache: dict) -> Optional[float]:
    """Fast IF lookup from pre-computed OpenAlex data."""
    if issn in cache:
        return cache[issn]
    row = db.fetchone(
        "SELECT two_year_mean_citedness FROM journals_openalex WHERE issns LIKE ?",
        (f"%{issn}%",)
    )
    cache[issn] = row["two_year_mean_citedness"] if row else None
    return cache[issn]


@cli.command("search", aliases=["s"], context_settings=CONTEXT_SETTINGS)
@click.argument("query")
@click.option("-n", "--number", "limit", default=10, show_default=True, help="Number of results")
@click.option("-o", "--offset", default=0, help="Skip first N results")
@click.option("-a", "--abstracts", is_flag=True, help="Show abstracts")
@click.option("-A", "--authors", is_flag=True, help="Show authors")
@click.option("-if", "--impact-factor", "with_if", is_flag=True, help="Show journal impact factor")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search_cmd(query: str, limit: int, offset: int, abstracts: bool, authors: bool, with_if: bool, as_json: bool):
    """Search for works by title, abstract, or authors."""
    from .db import get_db
    results = search(query, limit=limit, offset=offset)

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


@cli.command("get", aliases=["g"], context_settings=CONTEXT_SETTINGS)
@click.argument("doi")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--citation", is_flag=True, help="Output as citation")
def get_cmd(doi: str, as_json: bool, citation: bool):
    """Get a work by DOI."""
    work = get(doi)

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


@cli.command("count", aliases=["c"], context_settings=CONTEXT_SETTINGS)
@click.argument("query")
def count_cmd(query: str):
    """Count matching works."""
    n = count(query)
    click.echo(f"{n:,}")


@cli.command("info", aliases=["i"], context_settings=CONTEXT_SETTINGS)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def info_cmd(as_json: bool):
    """Show database/API information."""
    db_info = info()

    if as_json:
        click.echo(json.dumps(db_info, indent=2))
    else:
        mode = db_info.get("mode", "local")
        if mode == "remote":
            click.echo("CrossRef Local API (Remote)")
            click.echo("-" * 40)
            click.echo(f"API URL: {db_info.get('api_url', 'unknown')}")
            click.echo(f"Status: {db_info.get('status', 'unknown')}")
        else:
            click.echo("CrossRef Local Database")
            click.echo("-" * 40)
            click.echo(f"Database: {db_info.get('db_path', 'unknown')}")
            click.echo(f"Works: {db_info.get('works', 0):,}")
            click.echo(f"FTS indexed: {db_info.get('fts_indexed', 0):,}")
            click.echo(f"Citations: {db_info.get('citations', 0):,}")


@cli.command("impact-factor", aliases=["if"], context_settings=CONTEXT_SETTINGS)
@click.argument("journal")
@click.option("-y", "--year", default=2023, help="Target year")
@click.option("-w", "--window", default=2, help="Citation window years")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def impact_factor_cmd(journal: str, year: int, window: int, as_json: bool):
    """Calculate impact factor for a journal."""
    with ImpactFactorCalculator() as calc:
        result = calc.calculate_impact_factor(
            journal_identifier=journal,
            target_year=year,
            window_years=window,
        )

    if as_json:
        click.echo(json.dumps(result, indent=2))
    else:
        click.echo(f"Journal: {result['journal']}")
        click.echo(f"Year: {result['target_year']}")
        click.echo(f"Window: {result['window_range']}")
        click.echo(f"Articles: {result['total_articles']:,}")
        click.echo(f"Citations: {result['total_citations']:,}")
        click.echo(f"Impact Factor: {result['impact_factor']:.3f}")


@cli.command(context_settings=CONTEXT_SETTINGS)
def setup():
    """Check setup status and configuration."""
    from .config import DEFAULT_DB_PATHS, DEFAULT_API_URLS
    import os

    click.echo("CrossRef Local - Setup Status")
    click.echo("=" * 50)
    click.echo()

    # Check environment variables
    click.echo("Environment Variables:")
    env_db = os.environ.get("CROSSREF_LOCAL_DB")
    env_api = os.environ.get("CROSSREF_LOCAL_API")
    env_mode = os.environ.get("CROSSREF_LOCAL_MODE")

    if env_db:
        status = "OK" if os.path.exists(env_db) else "NOT FOUND"
        click.echo(f"  CROSSREF_LOCAL_DB: {env_db} ({status})")
    else:
        click.echo("  CROSSREF_LOCAL_DB: (not set)")

    if env_api:
        click.echo(f"  CROSSREF_LOCAL_API: {env_api}")
    else:
        click.echo("  CROSSREF_LOCAL_API: (not set)")

    if env_mode:
        click.echo(f"  CROSSREF_LOCAL_MODE: {env_mode}")

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

    # Check remote API endpoints
    click.echo("Remote API Endpoints:")
    api_found = None
    for url in DEFAULT_API_URLS:
        try:
            import urllib.request

            req = urllib.request.Request(f"{url}/health", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                if resp.status == 200:
                    click.echo(f"  [OK] {url}")
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
        click.echo(f"Remote API available: {api_found}")
        click.echo()
        click.echo("Ready! Try:")
        click.echo('  crossref-local --remote search "machine learning"')
        click.echo()
        click.echo("Or set environment:")
        click.echo("  export CROSSREF_LOCAL_MODE=remote")
    else:
        click.echo("No database or API found!")
        click.echo()
        click.echo("Options:")
        click.echo("  1. Local database:")
        click.echo("     export CROSSREF_LOCAL_DB=/path/to/crossref.db")
        click.echo()
        click.echo("  2. Remote API (via SSH tunnel):")
        click.echo("     ssh -L 3333:127.0.0.1:3333 your-nas")
        click.echo("     crossref-local --remote search 'query'")


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-t",
    "--transport",
    type=click.Choice(["stdio", "sse", "http"]),
    default="stdio",
    help="Transport protocol (stdio for Claude Desktop)",
)
@click.option("--host", default="localhost", help="Host for HTTP/SSE transport")
@click.option("--port", default=8082, type=int, help="Port for HTTP/SSE transport")
def serve(transport: str, host: str, port: int):
    """Run MCP server for Claude integration.

    \b
    Claude Desktop configuration (claude_desktop_config.json):
      {
        "mcpServers": {
          "crossref": {
            "command": "crossref-local",
            "args": ["serve"]
          }
        }
      }

    \b
    Or with explicit path:
      {
        "mcpServers": {
          "crossref": {
            "command": "python",
            "args": ["-m", "crossref_local.mcp_server"]
          }
        }
      }
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


@cli.command(context_settings=CONTEXT_SETTINGS)
@click.option("--host", default="0.0.0.0", help="Host to bind")
@click.option("--port", default=3333, type=int, help="Port to listen on")
def api(host: str, port: int):
    """Run HTTP API server with FTS5 search.

    \b
    This runs a FastAPI server that provides proper full-text search
    using FTS5 index across all 167M+ papers.

    \b
    Example:
      crossref-local api                  # Run on 0.0.0.0:3333
      crossref-local api --port 8080      # Custom port

    \b
    Then from a client:
      curl "http://localhost:3333/search?q=CRISPR&limit=10"
      curl "http://localhost:3333/get/10.1038/nature12373"
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
