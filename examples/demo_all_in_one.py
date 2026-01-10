#!/usr/bin/env python3
"""
CrossRef Local - All-in-One Demo

Demonstrates all main features:
- Full-text search (FTS5)
- DOI lookup
- Count queries
- Database info
- Impact factor calculation

Usage:
    python examples/demo_all_in_one.py
    python examples/demo_all_in_one.py --query "neural networks"
"""

import argparse
import sys
import time
from pathlib import Path

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from crossref_local import search, get, count, info, exists


def separator(title: str) -> None:
    """Print section separator."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_info() -> dict:
    """Demo: Database information."""
    separator("Database Info")

    db_info = info()
    print(f"Database: {db_info['db_path']}")
    print(f"Works:    {db_info['works']:,}")
    print(f"FTS:      {db_info['fts_indexed']:,}")
    print(f"Citations: {db_info['citations']:,}")

    return db_info


def demo_search(query: str, limit: int = 5) -> None:
    """Demo: Full-text search."""
    separator(f"Search: '{query}'")

    start = time.perf_counter()
    results = search(query, limit=limit)
    elapsed = (time.perf_counter() - start) * 1000

    print(f"Found {results.total:,} matches in {elapsed:.1f}ms")
    print(f"Showing top {len(results.works)} results:\n")

    for i, work in enumerate(results.works, 1):
        print(f"{i}. {work.title}")
        print(f"   Authors: {', '.join(work.authors[:3])}" +
              (" ..." if len(work.authors) > 3 else ""))
        print(f"   Year: {work.year} | DOI: {work.doi}")
        print()


def demo_get(doi: str) -> None:
    """Demo: Get work by DOI."""
    separator(f"Get DOI: {doi}")

    work = get(doi)

    if work:
        print(f"Title:   {work.title}")
        print(f"Authors: {', '.join(work.authors)}")
        print(f"Year:    {work.year}")
        print(f"Journal: {work.journal}")
        print(f"Type:    {work.type}")
        print(f"\nCitation:")
        print(f"  {work.citation()}")
    else:
        print(f"DOI not found: {doi}")


def demo_count(queries: list) -> None:
    """Demo: Count matches for multiple queries."""
    separator("Count Queries")

    print(f"{'Query':<40} {'Matches':>15} {'Time':>10}")
    print("-" * 67)

    for query in queries:
        start = time.perf_counter()
        n = count(query)
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{query:<40} {n:>15,} {elapsed:>8.1f}ms")


def demo_exists(dois: list) -> None:
    """Demo: Check if DOIs exist."""
    separator("Check DOI Existence")

    for doi in dois:
        result = "✓ Found" if exists(doi) else "✗ Not found"
        print(f"{doi}: {result}")


def demo_impact_factor() -> None:
    """Demo: Impact factor calculation."""
    separator("Impact Factor Calculation")

    try:
        from crossref_local.impact_factor import ImpactFactorCalculator

        journals = ["Nature", "Science", "Cell"]

        with ImpactFactorCalculator() as calc:
            print(f"{'Journal':<20} {'IF (2023)':>12}")
            print("-" * 34)

            for journal in journals:
                try:
                    result = calc.calculate_impact_factor(journal, target_year=2023)
                    if result and result.get('impact_factor'):
                        print(f"{journal:<20} {result['impact_factor']:>12.3f}")
                    else:
                        print(f"{journal:<20} {'N/A':>12}")
                except Exception as e:
                    print(f"{journal:<20} {'Error':>12}")

    except ImportError:
        print("Impact factor module not available")
    except Exception as e:
        print(f"Impact factor calculation failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="CrossRef Local - All-in-One Demo")
    parser.add_argument("-q", "--query", default="hippocampal sharp wave ripples",
                        help="Search query (default: hippocampal sharp wave ripples)")
    parser.add_argument("-n", "--limit", type=int, default=5,
                        help="Number of search results (default: 5)")
    parser.add_argument("--skip-if", action="store_true",
                        help="Skip impact factor demo")
    args = parser.parse_args()

    print("\n" + "="*60)
    print("  CROSSREF LOCAL - ALL-IN-ONE DEMO")
    print("="*60)

    # 1. Database info
    db_info = demo_info()

    if db_info['works'] == 0:
        print("\n⚠️  Database is empty or not found.")
        print("   Run: crossref-local setup")
        return 1

    # 2. Full-text search
    demo_search(args.query, limit=args.limit)

    # 3. Get by DOI (find one from search first)
    results = search(args.query, limit=1)
    if results.works:
        demo_get(results.works[0].doi)

    # 4. Count queries
    demo_count([
        "machine learning",
        "CRISPR",
        "climate change",
        "quantum computing",
        "neural network",
    ])

    # 5. Check DOI existence
    demo_exists([
        "10.1038/nature12373",
        "10.1126/science.aax0758",
        "10.9999/nonexistent.doi",
    ])

    # 6. Impact factor (optional)
    if not args.skip_if:
        demo_impact_factor()

    separator("Demo Complete")
    print("For more examples, see:")
    print("  - examples/demo_all_in_one.ipynb")
    print("  - examples/demo_cli.sh")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
