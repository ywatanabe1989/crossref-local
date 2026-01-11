"""Command-line interface for crossref_local."""

import click
import json
import re
import sys
from typing import Optional

from . import search, get, count, info, __version__


from .impact_factor import ImpactFactorCalculator


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
def cli():
    """Local CrossRef database with 167M+ works and full-text search."""
    pass


@cli.command(aliases=["s"], context_settings=CONTEXT_SETTINGS)
@click.argument("query")
@click.option("-n", "--limit", default=10, help="Number of results")
@click.option("-o", "--offset", default=0, help="Skip first N results")
@click.option("-a", "--with-abstracts", is_flag=True, help="Show abstracts")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def search_cmd(query: str, limit: int, offset: int, with_abstracts: bool, as_json: bool):
    """Search for works by title, abstract, or authors."""
    results = search(query, limit=limit, offset=offset)

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
            if work.journal:
                click.echo(f"   Journal: {work.journal}")
            if with_abstracts and work.abstract:
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


@cli.command(aliases=["c"], context_settings=CONTEXT_SETTINGS)
@click.argument("query")
def count_cmd(query: str):
    """Count matching works."""
    n = count(query)
    click.echo(f"{n:,}")


@cli.command(aliases=["i"], context_settings=CONTEXT_SETTINGS)
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def info_cmd(as_json: bool):
    """Show database information."""
    db_info = info()

    if as_json:
        click.echo(json.dumps(db_info, indent=2))
    else:
        click.echo("CrossRef Local Database")
        click.echo("-" * 40)
        click.echo(f"Database: {db_info['db_path']}")
        click.echo(f"Works: {db_info['works']:,}")
        click.echo(f"FTS indexed: {db_info['fts_indexed']:,}")
        click.echo(f"Citations: {db_info['citations']:,}")


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
    from .config import Config, DEFAULT_DB_PATHS
    import os

    click.echo("CrossRef Local - Setup Status")
    click.echo("=" * 50)
    click.echo()

    # Check environment variable
    env_db = os.environ.get("CROSSREF_LOCAL_DB")
    if env_db:
        click.echo(f"CROSSREF_LOCAL_DB: {env_db}")
        if os.path.exists(env_db):
            click.echo("  Status: OK")
        else:
            click.echo("  Status: NOT FOUND")
    else:
        click.echo("CROSSREF_LOCAL_DB: (not set)")

    click.echo()

    # Check default paths
    click.echo("Checking default database locations:")
    db_found = None
    for path in DEFAULT_DB_PATHS:
        if path.exists():
            click.echo(f"  [OK] {path}")
            if db_found is None:
                db_found = path
        else:
            click.echo(f"  [ ] {path}")

    click.echo()

    if db_found:
        click.echo(f"Database found: {db_found}")
        click.echo()

        try:
            db_info = info()
            click.echo(f"  Works: {db_info['works']:,}")
            click.echo(f"  FTS indexed: {db_info['fts_indexed']:,}")
            click.echo(f"  Citations: {db_info['citations']:,}")
            click.echo()
            click.echo("Setup complete! Try:")
            click.echo('  crossref-local search "machine learning"')
        except Exception as e:
            click.echo(f"  Error reading database: {e}", err=True)
    else:
        click.echo("No database found!")
        click.echo()
        click.echo("To set up:")
        click.echo("  export CROSSREF_LOCAL_DB=/path/to/crossref.db")
        click.echo("  See: make db-build-info")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
