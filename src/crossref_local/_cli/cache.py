"""CLI commands for cache management.

This module provides cache-related CLI commands that are registered
with the main CLI application.
"""

import json
import click


def register_cache_commands(cli_group):
    """Register cache commands with the CLI group."""

    @cli_group.group()
    def cache():
        """Manage paper caches for efficient querying."""
        pass

    @cache.command("create")
    @click.argument("name")
    @click.option("-q", "--query", required=True, help="FTS search query")
    @click.option("-l", "--limit", default=1000, help="Max papers to cache")
    @click.option("--json", "as_json", is_flag=True, help="Output as JSON")
    def cache_create(name, query, limit, as_json):
        """Create a cache from search query.

        Example:
            crossref-local cache create epilepsy -q "epilepsy seizure" -l 500
        """
        from . import cache as cache_module

        info = cache_module.create(name, query=query, limit=limit)
        if as_json:
            click.echo(json.dumps(info.to_dict(), indent=2))
        else:
            click.echo(f"Created cache: {info.name}")
            click.echo(f"  Papers: {info.paper_count}")
            click.echo(f"  Size: {info.size_bytes / 1024 / 1024:.2f} MB")
            click.echo(f"  Path: {info.path}")

    @cache.command("list")
    @click.option("--json", "as_json", is_flag=True, help="Output as JSON")
    def cache_list(as_json):
        """List all available caches."""
        from . import cache as cache_module

        caches = cache_module.list_caches()
        if as_json:
            click.echo(json.dumps([c.to_dict() for c in caches], indent=2))
        else:
            if not caches:
                click.echo("No caches found.")
                return
            for c in caches:
                click.echo(
                    f"{c.name}: {c.paper_count} papers, {c.size_bytes / 1024 / 1024:.2f} MB"
                )

    @cache.command("query")
    @click.argument("name")
    @click.option("-f", "--fields", help="Comma-separated field list")
    @click.option("--abstract", is_flag=True, help="Include abstracts")
    @click.option("--refs", is_flag=True, help="Include references")
    @click.option("--citations", is_flag=True, help="Include citation counts")
    @click.option("--year-min", type=int, help="Minimum year filter")
    @click.option("--year-max", type=int, help="Maximum year filter")
    @click.option("--journal", help="Journal name filter")
    @click.option("-l", "--limit", type=int, help="Max results")
    @click.option("--json", "as_json", is_flag=True, help="Output as JSON")
    def cache_query(
        name,
        fields,
        abstract,
        refs,
        citations,
        year_min,
        year_max,
        journal,
        limit,
        as_json,
    ):
        """Query cache with field filtering.

        Examples:
            crossref-local cache query epilepsy -f doi,title,year
            crossref-local cache query epilepsy --year-min 2020 --citations
        """
        from . import cache as cache_module

        field_list = fields.split(",") if fields else None
        papers = cache_module.query(
            name,
            fields=field_list,
            include_abstract=abstract,
            include_references=refs,
            include_citations=citations,
            year_min=year_min,
            year_max=year_max,
            journal=journal,
            limit=limit,
        )

        if as_json:
            click.echo(json.dumps(papers, indent=2))
        else:
            click.echo(f"Found {len(papers)} papers")
            for p in papers[:10]:
                title = p.get("title", "No title")[:60]
                year = p.get("year", "?")
                click.echo(f"  [{year}] {title}...")
            if len(papers) > 10:
                click.echo(f"  ... and {len(papers) - 10} more")

    @cache.command("stats")
    @click.argument("name")
    @click.option("--json", "as_json", is_flag=True, help="Output as JSON")
    def cache_stats(name, as_json):
        """Show cache statistics."""
        from . import cache as cache_module

        stats = cache_module.stats(name)
        if as_json:
            click.echo(json.dumps(stats, indent=2))
        else:
            click.echo(f"Papers: {stats['paper_count']}")
            yr = stats.get("year_range", {})
            click.echo(f"Years: {yr.get('min', '?')} - {yr.get('max', '?')}")
            click.echo(f"Abstracts: {stats['abstract_coverage']}%")
            click.echo("\nTop journals:")
            for j in stats.get("top_journals", [])[:5]:
                click.echo(f"  {j['journal']}: {j['count']}")

    @cache.command("export")
    @click.argument("name")
    @click.argument("output")
    @click.option(
        "--format", "fmt", default="json", help="Format: json, csv, bibtex, dois"
    )
    @click.option("-f", "--fields", help="Comma-separated field list")
    def cache_export(name, output, fmt, fields):
        """Export cache to file.

        Examples:
            crossref-local cache export epilepsy papers.csv --format csv
            crossref-local cache export epilepsy refs.bib --format bibtex
        """
        from . import cache as cache_module

        field_list = fields.split(",") if fields else None
        path = cache_module.export(name, output, format=fmt, fields=field_list)
        click.echo(f"Exported to: {path}")

    @cache.command("delete")
    @click.argument("name")
    @click.option("--yes", is_flag=True, help="Skip confirmation")
    def cache_delete(name, yes):
        """Delete a cache."""
        from . import cache as cache_module

        if not yes:
            if not click.confirm(f"Delete cache '{name}'?"):
                return

        if cache_module.delete(name):
            click.echo(f"Deleted: {name}")
        else:
            click.echo(f"Cache not found: {name}")

    @cache.command("dois")
    @click.argument("name")
    def cache_dois(name):
        """Output DOIs from cache (one per line)."""
        from . import cache as cache_module

        dois = cache_module.query_dois(name)
        for doi in dois:
            click.echo(doi)

    return cache
