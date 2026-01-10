# Add your tests here


if __name__ == "__main__":
    import os
    import pytest
    pytest.main([os.path.abspath(__file__)])

# --------------------------------------------------------------------------------
# Start of Source Code from: /home/ywatanabe/proj/crossref_local/src/crossref_local/cli.py
# --------------------------------------------------------------------------------
# """Command-line interface for crossref_local."""
# 
# import click
# import json
# import sys
# from typing import Optional
# 
# from . import search, get, count, info, __version__
# from .impact_factor import ImpactFactorCalculator
# 
# 
# @click.group()
# @click.version_option(version=__version__, prog_name="crossref-local")
# def cli():
#     """Local CrossRef database with 167M+ works and full-text search."""
#     pass
# 
# 
# @cli.command()
# @click.argument("query")
# @click.option("-n", "--limit", default=10, help="Number of results (default: 10)")
# @click.option("-o", "--offset", default=0, help="Skip first N results")
# @click.option("--json", "as_json", is_flag=True, help="Output as JSON")
# def search_cmd(query: str, limit: int, offset: int, as_json: bool):
#     """Search for works by title, abstract, or authors.
# 
#     Examples:
# 
#         crossref-local search "hippocampal sharp wave ripples"
# 
#         crossref-local search "machine learning" -n 20
# 
#         crossref-local search "CRISPR" --json
#     """
#     results = search(query, limit=limit, offset=offset)
# 
#     if as_json:
#         output = {
#             "query": results.query,
#             "total": results.total,
#             "elapsed_ms": results.elapsed_ms,
#             "works": [w.to_dict() for w in results.works],
#         }
#         click.echo(json.dumps(output, indent=2))
#     else:
#         click.echo(f"Found {results.total:,} matches in {results.elapsed_ms:.1f}ms\n")
#         for i, work in enumerate(results.works, start=offset + 1):
#             title = work.title or "Untitled"
#             year = f"({work.year})" if work.year else ""
#             click.echo(f"{i}. {title} {year}")
#             click.echo(f"   DOI: {work.doi}")
#             if work.journal:
#                 click.echo(f"   Journal: {work.journal}")
#             click.echo()
# 
# 
# @cli.command("get")
# @click.argument("doi")
# @click.option("--json", "as_json", is_flag=True, help="Output as JSON")
# @click.option("--citation", is_flag=True, help="Output as citation")
# def get_cmd(doi: str, as_json: bool, citation: bool):
#     """Get a work by DOI.
# 
#     Examples:
# 
#         crossref-local get 10.1126/science.aax0758
# 
#         crossref-local get 10.1038/nature12373 --json
# 
#         crossref-local get 10.1126/science.aax0758 --citation
#     """
#     work = get(doi)
# 
#     if work is None:
#         click.echo(f"DOI not found: {doi}", err=True)
#         sys.exit(1)
# 
#     if as_json:
#         click.echo(json.dumps(work.to_dict(), indent=2))
#     elif citation:
#         click.echo(work.citation())
#     else:
#         click.echo(f"Title: {work.title}")
#         click.echo(f"Authors: {', '.join(work.authors)}")
#         click.echo(f"Year: {work.year}")
#         click.echo(f"Journal: {work.journal}")
#         click.echo(f"DOI: {work.doi}")
#         if work.citation_count:
#             click.echo(f"Citations: {work.citation_count}")
# 
# 
# @cli.command()
# @click.argument("query")
# def count_cmd(query: str):
#     """Count matching works without fetching results.
# 
#     Example:
# 
#         crossref-local count "machine learning"
#     """
#     n = count(query)
#     click.echo(f"{n:,}")
# 
# 
# @cli.command()
# @click.option("--json", "as_json", is_flag=True, help="Output as JSON")
# def info_cmd(as_json: bool):
#     """Show database information.
# 
#     Example:
# 
#         crossref-local info
#     """
#     db_info = info()
# 
#     if as_json:
#         click.echo(json.dumps(db_info, indent=2))
#     else:
#         click.echo("CrossRef Local Database")
#         click.echo("-" * 40)
#         click.echo(f"Database: {db_info['db_path']}")
#         click.echo(f"Works: {db_info['works']:,}")
#         click.echo(f"FTS indexed: {db_info['fts_indexed']:,}")
#         click.echo(f"Citations: {db_info['citations']:,}")
# 
# 
# @cli.command("impact-factor")
# @click.argument("journal")
# @click.option("-y", "--year", default=2023, help="Target year (default: 2023)")
# @click.option("-w", "--window", default=2, help="Citation window in years (default: 2)")
# @click.option("--json", "as_json", is_flag=True, help="Output as JSON")
# def impact_factor_cmd(journal: str, year: int, window: int, as_json: bool):
#     """Calculate impact factor for a journal.
# 
#     Examples:
# 
#         crossref-local impact-factor Nature
# 
#         crossref-local impact-factor Science -y 2022
# 
#         crossref-local impact-factor "Cell" -w 5 --json
#     """
#     with ImpactFactorCalculator() as calc:
#         result = calc.calculate_impact_factor(
#             journal_identifier=journal,
#             target_year=year,
#             window_years=window,
#         )
# 
#     if as_json:
#         click.echo(json.dumps(result, indent=2))
#     else:
#         click.echo(f"Journal: {result['journal']}")
#         click.echo(f"Year: {result['target_year']}")
#         click.echo(f"Window: {result['window_range']}")
#         click.echo(f"Articles: {result['total_articles']:,}")
#         click.echo(f"Citations: {result['total_citations']:,}")
#         click.echo(f"Impact Factor: {result['impact_factor']:.3f}")
# 
# 
# # Aliases for convenience
# cli.add_command(search_cmd, name="s")
# cli.add_command(get_cmd, name="g")
# cli.add_command(count_cmd, name="c")
# cli.add_command(info_cmd, name="i")
# cli.add_command(impact_factor_cmd, name="if")
# 
# 
# def main():
#     """Entry point for CLI."""
#     cli()
# 
# 
# if __name__ == "__main__":
#     main()

# --------------------------------------------------------------------------------
# End of Source Code from: /home/ywatanabe/proj/crossref_local/src/crossref_local/cli.py
# --------------------------------------------------------------------------------
