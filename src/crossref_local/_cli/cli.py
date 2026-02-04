"""Command-line interface for crossref_local."""

import sys

import click
from rich.console import Console

from .. import __version__, info

console = Console()


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
    from .._core.config import Config

    ctx.ensure_object(dict)

    if api_url:
        Config.set_api_url(api_url)
    elif http:
        Config.set_mode("http")


# Register search commands from search module
from .search import search_by_doi_cmd, search_cmd

cli.add_command(search_cmd)
cli.add_command(search_by_doi_cmd)


@cli.command(context_settings=CONTEXT_SETTINGS)
def status():
    """Show status and configuration."""
    import os

    from .._core.config import DEFAULT_API_URLS, DEFAULT_DB_PATHS

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
            "Host for relay server (default: 0.0.0.0)",
            os.environ.get("CROSSREF_LOCAL_HOST"),
        ),
        (
            "CROSSREF_LOCAL_PORT",
            "Port for relay server (default: 31291)",
            os.environ.get("CROSSREF_LOCAL_PORT"),
        ),
    ]

    for var_name, description, value in env_vars:
        if value:
            if var_name == "CROSSREF_LOCAL_DB":
                stat = " (OK)" if os.path.exists(value) else " (NOT FOUND)"
            else:
                stat = ""
            click.echo(f"  {var_name}={value}{stat}")
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
    for url in DEFAULT_API_URLS:
        try:
            import json as json_module
            import urllib.request

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
                    else:
                        click.echo(
                            f"  [WARN] {url} (v{server_version} != v{__version__})"
                        )
                        click.echo(
                            "         Server version mismatch - may be incompatible"
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


# Register MCP subcommand group
from .mcp import mcp, run_mcp_server

cli.add_command(mcp)


# Backward compatibility alias (hidden)
@cli.command("run-server-mcp", context_settings=CONTEXT_SETTINGS, hidden=True)
@click.option(
    "-t", "--transport", type=click.Choice(["stdio", "sse", "http"]), default="stdio"
)
@click.option("--host", default="localhost", envvar="CROSSREF_LOCAL_MCP_HOST")
@click.option("--port", default=8082, type=int, envvar="CROSSREF_LOCAL_MCP_PORT")
def serve_mcp(transport: str, host: str, port: int):
    """Run MCP server (deprecated: use 'mcp start' instead)."""
    click.echo(
        "Note: 'run-server-mcp' is deprecated. Use 'crossref-local mcp start'.",
        err=True,
    )
    run_mcp_server(transport, host, port)


@cli.command("relay", context_settings=CONTEXT_SETTINGS)
@click.option("--host", default=None, envvar="CROSSREF_LOCAL_HOST", help="Host to bind")
@click.option(
    "--port",
    default=None,
    type=int,
    envvar="CROSSREF_LOCAL_PORT",
    help="Port to listen on (default: 31291)",
)
@click.option(
    "--force",
    is_flag=True,
    help="Kill existing process using the port if any",
)
def relay(host: str, port: int, force: bool):
    """Run HTTP relay server for remote database access.

    \b
    This runs a FastAPI server that provides proper full-text search
    using FTS5 index across all 167M+ papers.

    \b
    Example:
      crossref-local relay                  # Run on 0.0.0.0:31291
      crossref-local relay --port 8080      # Custom port
      crossref-local relay --force          # Kill existing process if port in use

    \b
    Then connect with http mode:
      crossref-local --http search "CRISPR"
      curl "http://localhost:8333/works?q=CRISPR&limit=10"
    """
    try:
        from .._server import run_server
    except ImportError:
        click.echo(
            "API server requires fastapi and uvicorn. Install with:\n"
            "  pip install fastapi uvicorn",
            err=True,
        )
        sys.exit(1)

    from .._server import DEFAULT_HOST, DEFAULT_PORT

    host = host or DEFAULT_HOST
    port = port or DEFAULT_PORT

    # Handle force flag
    if force:
        from .utils import kill_process_on_port

        kill_process_on_port(port)

    click.echo(f"Starting CrossRef Local relay server on {host}:{port}")
    click.echo(f"Search endpoint: http://{host}:{port}/works?q=<query>")
    click.echo(f"Docs: http://{host}:{port}/docs")
    run_server(host=host, port=port)


# Deprecated alias for backwards compatibility
@cli.command("run-server-http", context_settings=CONTEXT_SETTINGS, hidden=True)
@click.option("--host", default=None, envvar="CROSSREF_LOCAL_HOST")
@click.option("--port", default=None, type=int, envvar="CROSSREF_LOCAL_PORT")
@click.pass_context
def run_server_http_deprecated(ctx, host: str, port: int):
    """Deprecated: Use 'crossref-local relay' instead."""
    click.echo(
        "Note: 'run-server-http' is deprecated. Use 'crossref-local relay'.",
        err=True,
    )
    ctx.invoke(relay, host=host, port=port)


@cli.command("list-apis", context_settings=CONTEXT_SETTINGS)
@click.option(
    "-v", "--verbose", count=True, help="Verbosity: -v sig, -vv +doc, -vvv full"
)
@click.option("-d", "--max-depth", type=int, default=5, help="Max recursion depth")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def list_apis(verbose, max_depth, as_json):
    """List Python APIs (alias for: scitex introspect api crossref_local)."""
    try:
        from scitex.cli.introspect import api

        ctx = click.Context(api)
        ctx.invoke(
            api,
            dotted_path="crossref_local",
            verbose=verbose,
            max_depth=max_depth,
            as_json=as_json,
        )
    except ImportError:
        # Fallback if scitex not installed
        click.echo("Install scitex for full API introspection:")
        click.echo("  pip install scitex")
        click.echo()
        click.echo("Or use: scitex introspect api crossref_local")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
