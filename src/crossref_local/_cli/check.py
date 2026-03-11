"""CLI command for citation checking."""

import json
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@click.command("check", context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("input", type=click.Path(), required=False)
@click.option("-d", "--doi", multiple=True, help="Check specific DOI(s)")
@click.option(
    "-f",
    "--format",
    type=click.Choice(["bibtex", "doi-list", "auto"]),
    default="auto",
    help="Input format (default: auto-detect)",
)
@click.option("--no-validate", is_flag=True, help="Skip metadata validation")
@click.option("--no-suggest", is_flag=True, help="Skip enrichment suggestions")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
@click.option("--save", "save_path", type=click.Path(), help="Save results to file")
@click.option(
    "--save-format",
    type=click.Choice(["json", "text"]),
    default="json",
    help="Format for --save output",
)
def check_cmd(
    input, doi, format, no_validate, no_suggest, as_json, save_path, save_format
):
    """Check citations against the local CrossRef database.

    \b
    Accepts BibTeX files, DOI list files, or direct DOIs.

    \b
    Examples:
      crossref-local check bibliography.bib
      crossref-local check dois.txt
      crossref-local check -d 10.1038/nature12373
      crossref-local check bibliography.bib --json
      crossref-local check bibliography.bib --save report.json
    """
    from .._core.checker import check_bibtex, check_citations, check_doi_list

    validate = not no_validate
    suggest = not no_suggest

    if doi:
        result = check_citations(
            list(doi), validate_metadata=validate, suggest_enrichment=suggest
        )
    elif input:
        # Auto-detect format
        if format == "auto":
            format = "bibtex" if input.endswith(".bib") else "doi-list"

        if format == "bibtex":
            result = check_bibtex(
                input, validate_metadata=validate, suggest_enrichment=suggest
            )
        else:
            result = check_doi_list(
                input, validate_metadata=validate, suggest_enrichment=suggest
            )
    else:
        # Read from stdin
        content = sys.stdin.read().strip()
        if not content:
            click.echo(
                "No input provided. Use: crossref-local check FILE or -d DOI", err=True
            )
            sys.exit(1)
        dois = [
            line.strip()
            for line in content.split("\n")
            if line.strip() and not line.startswith("#")
        ]
        result = check_citations(
            dois, validate_metadata=validate, suggest_enrichment=suggest
        )

    if as_json:
        click.echo(json.dumps(result.to_dict(), indent=2))
    else:
        _display_rich(result)

    if save_path:
        result.save(save_path, save_format)
        console.print(f"\nResults saved to: {save_path}")


def _display_rich(result):
    """Display results using Rich formatting."""
    # Summary
    pct_found = result.found / max(result.total, 1) * 100

    summary = Table.grid(padding=(0, 2))
    summary.add_row("Total:", f"{result.total} citations")
    summary.add_row("Found:", f"[green]{result.found}[/green] ({pct_found:.1f}%)")
    summary.add_row("Missing:", f"[red]{result.missing}[/red]")
    if result.with_issues:
        summary.add_row("With issues:", f"[yellow]{result.with_issues}[/yellow]")
    summary.add_row("Time:", f"{result.elapsed_ms:.1f}ms")
    console.print(Panel(summary, title="Citation Check", border_style="blue"))

    # Missing
    missing = [e for e in result.entries if not e.found]
    if missing:
        table = Table(
            title=f"Missing ({len(missing)})", show_header=True, border_style="red"
        )
        table.add_column("DOI / Identifier", style="red")
        table.add_column("Key")
        table.add_column("Issues")
        for e in missing:
            table.add_row(
                e.identifier[:60],
                e.source_key or "",
                "\n".join(e.issues),
            )
        console.print(table)

    # Issues
    with_issues = [e for e in result.entries if e.found and e.issues]
    if with_issues:
        table = Table(
            title=f"Issues ({len(with_issues)})",
            show_header=True,
            border_style="yellow",
        )
        table.add_column("DOI")
        table.add_column("Key")
        table.add_column("Issues", style="yellow")
        for e in with_issues:
            table.add_row(
                e.identifier[:50],
                e.source_key or "",
                "\n".join(e.issues),
            )
        console.print(table)

    if not missing and not with_issues:
        console.print("[green]All citations found with complete metadata.[/green]")
