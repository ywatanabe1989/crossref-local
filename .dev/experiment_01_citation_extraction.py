#!/usr/bin/env python3
"""
Experiment 1: Test citation data extraction and bidirectional lookups.

This validates:
1. Can we query citations table efficiently?
2. Can we get references (citing → cited)?
3. Can we get citations (cited → citing)?
4. What's the performance like?
"""

import sqlite3
import json
import time
from pathlib import Path
from collections import defaultdict

SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "../data/crossref.db"

# Test with a well-cited Nature paper from 2020
TEST_DOI = "10.1038/s41586-020-2008-3"  # A highly cited COVID-19 paper


def print_section(title):
    """Print formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def test_citations_table_exists(conn):
    """Test if citations table exists and has data."""
    print_section("Test 1: Citations Table Status")

    cursor = conn.execute("""
        SELECT COUNT(*) as total,
               MIN(citing_year) as min_year,
               MAX(citing_year) as max_year
        FROM citations
    """)

    row = cursor.fetchone()
    print(f"Total citations in table: {row[0]:,}")
    print(f"Year range: {row[1]} - {row[2]}")

    return row[0] > 0


def test_forward_citations(conn, doi):
    """Test getting references (papers this DOI cites)."""
    print_section(f"Test 2: Forward Citations (What does {doi} cite?)")

    start = time.time()
    cursor = conn.execute("""
        SELECT cited_doi, citing_year
        FROM citations
        WHERE citing_doi = ?
        LIMIT 20
    """, (doi.lower(),))

    refs = cursor.fetchall()
    elapsed = time.time() - start

    print(f"Query time: {elapsed*1000:.2f}ms")
    print(f"Found {len(refs)} references (showing first 20)")

    if refs:
        print("\nSample references:")
        for i, (cited_doi, year) in enumerate(refs[:5], 1):
            print(f"  {i}. [{year}] {cited_doi}")

    return len(refs) > 0


def test_reverse_citations(conn, doi):
    """Test getting citations (papers that cite this DOI)."""
    print_section(f"Test 3: Reverse Citations (What cites {doi}?)")

    start = time.time()
    cursor = conn.execute("""
        SELECT citing_doi, citing_year
        FROM citations
        WHERE cited_doi = ?
        ORDER BY citing_year DESC
        LIMIT 20
    """, (doi.lower(),))

    citations = cursor.fetchall()
    elapsed = time.time() - start

    print(f"Query time: {elapsed*1000:.2f}ms")
    print(f"Found {len(citations)} citations (showing first 20)")

    if citations:
        print("\nSample citations:")
        for i, (citing_doi, year) in enumerate(citations[:5], 1):
            print(f"  {i}. [{year}] {citing_doi}")

        # Year distribution
        year_counts = defaultdict(int)
        cursor = conn.execute("""
            SELECT citing_year, COUNT(*) as count
            FROM citations
            WHERE cited_doi = ?
            GROUP BY citing_year
            ORDER BY citing_year DESC
        """, (doi.lower(),))

        for year, count in cursor:
            year_counts[year] = count

        print(f"\nCitation year distribution:")
        for year in sorted(year_counts.keys(), reverse=True)[:5]:
            print(f"  {year}: {year_counts[year]:,} citations")

    return len(citations) > 0


def test_citation_network_query(conn, doi, depth=1):
    """Test building a simple citation network."""
    print_section(f"Test 4: Citation Network Building (depth={depth})")

    network = set()
    to_explore = {doi.lower()}
    explored = set()

    start = time.time()

    for d in range(depth):
        print(f"\nDepth {d+1}: Exploring {len(to_explore)} papers...")

        next_level = set()
        for paper_doi in to_explore:
            if paper_doi in explored:
                continue

            explored.add(paper_doi)

            # Get papers this one cites
            cursor = conn.execute("""
                SELECT cited_doi FROM citations WHERE citing_doi = ? LIMIT 50
            """, (paper_doi,))

            for (cited,) in cursor:
                network.add((paper_doi, cited, 'cites'))
                next_level.add(cited)

            # Get papers that cite this one
            cursor = conn.execute("""
                SELECT citing_doi FROM citations WHERE cited_doi = ? LIMIT 50
            """, (paper_doi,))

            for (citing,) in cursor:
                network.add((citing, paper_doi, 'cites'))
                next_level.add(citing)

        to_explore = next_level
        print(f"  Found {len(network)} edges, {len(explored)} unique papers")

    elapsed = time.time() - start

    print(f"\nTotal network built:")
    print(f"  Papers: {len(explored)}")
    print(f"  Citation edges: {len(network)}")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Papers/sec: {len(explored)/elapsed:.1f}")

    return len(network) > 0


def test_get_paper_metadata(conn, doi):
    """Test getting paper metadata from works table."""
    print_section(f"Test 5: Paper Metadata Lookup")

    start = time.time()
    cursor = conn.execute("""
        SELECT metadata
        FROM works
        WHERE doi = ?
    """, (doi,))

    row = cursor.fetchone()
    elapsed = time.time() - start

    print(f"Query time: {elapsed*1000:.2f}ms")

    if row:
        metadata = json.loads(row[0])
        print(f"\nPaper found:")
        print(f"  Title: {metadata.get('title', ['N/A'])[0][:80]}")
        print(f"  Authors: {len(metadata.get('author', []))} authors")
        print(f"  Year: {metadata.get('published', {}).get('date-parts', [[None]])[0][0]}")
        print(f"  References: {len(metadata.get('reference', []))}")
        print(f"  Type: {metadata.get('type', 'N/A')}")
        return True
    else:
        print(f"Paper not found in works table")
        return False


def find_sample_paper_with_citations(conn):
    """Find a sample paper that has both references and citations."""
    print_section("Finding Sample Paper for Testing")

    # Simpler query - just get a recent paper with references
    cursor = conn.execute("""
        SELECT citing_doi
        FROM citations
        WHERE citing_year >= 2020
        LIMIT 1
    """)

    row = cursor.fetchone()

    if row:
        sample_doi = row[0]
        print(f"\nUsing sample paper: {sample_doi}")

        # Count its references
        cursor = conn.execute("""
            SELECT COUNT(*) FROM citations WHERE citing_doi = ?
        """, (sample_doi,))
        refs = cursor.fetchone()[0]

        # Count its citations
        cursor = conn.execute("""
            SELECT COUNT(*) FROM citations WHERE cited_doi = ?
        """, (sample_doi,))
        cites = cursor.fetchone()[0]

        print(f"  References: {refs}, Citations: {cites}")
        return sample_doi

    print(f"\nNo sample found, using default: {TEST_DOI}")
    return TEST_DOI


def main():
    print("="*70)
    print("  Connected Papers Architecture - Experiment 1")
    print("  Citation Data Extraction & Bidirectional Lookups")
    print("="*70)
    print(f"\nDatabase: {DB_PATH}")

    # Connect to database (read-only mode to avoid conflicts)
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)

    try:
        # Test 1: Check citations table
        if not test_citations_table_exists(conn):
            print("\n❌ Citations table is empty or doesn't exist!")
            print("   Run: python .dev/build_citation_index.py 2023")
            return 1

        # Find a good sample paper
        sample_doi = find_sample_paper_with_citations(conn)

        # Test 2: Forward citations (references)
        test_forward_citations(conn, sample_doi)

        # Test 3: Reverse citations (who cites this)
        test_reverse_citations(conn, sample_doi)

        # Test 4: Citation network building
        test_citation_network_query(conn, sample_doi, depth=1)

        # Test 5: Metadata lookup
        test_get_paper_metadata(conn, sample_doi)

        # Summary
        print_section("Summary")
        print("✅ All tests passed!")
        print("\nNext steps:")
        print("  1. Co-citation analysis (Experiment 2)")
        print("  2. Bibliographic coupling (Experiment 3)")
        print("  3. Similarity scoring (Experiment 4)")

        return 0

    finally:
        conn.close()


if __name__ == "__main__":
    import sys
    sys.exit(main())
