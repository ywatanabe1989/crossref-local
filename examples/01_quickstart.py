#!/usr/bin/env python3
"""
CrossRef Local - Demo for the LLM Era

Key features that matter for AI research assistants:
1. ABSTRACTS - Full text for LLM context (not available in many APIs)
2. IMPACT FACTOR - Journal quality assessment
3. CITATIONS - Paper importance metrics
4. SPEED - 167M records in milliseconds, no rate limits

Usage:
    python examples/demo_wow.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from crossref_local import search, get, count, info


def section(title: str) -> None:
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}\n")


def demo():
    db = info()

    print("\n" + "━"*70)
    print("  🔬 CROSSREF LOCAL - Research Database for the LLM Era")
    print("━"*70)
    print(f"\n  📊 {db['works']:,} scholarly works | {db['citations']:,} citations indexed\n")

    # =========================================================================
    # 1. ABSTRACTS - The key differentiator for LLMs
    # =========================================================================
    section("1️⃣  ABSTRACTS - Full Text for LLM Context")

    print("  Unlike many APIs, CrossRef includes abstracts - essential for LLMs.\n")

    results = search("hippocampal memory consolidation", limit=2)

    for work in results.works:
        print(f"  📄 {work.title[:65]}...")
        print(f"     {work.journal} ({work.year})")
        print()
        if work.abstract:
            # Show first 200 chars of abstract
            abstract_preview = work.abstract[:200].replace('\n', ' ')
            print(f"     📝 Abstract: {abstract_preview}...")
        else:
            print("     📝 Abstract: [Available in full record]")
        print()

    print("  → LLMs can understand paper content, not just metadata!\n")

    # =========================================================================
    # 2. IMPACT FACTOR - Journal Quality Assessment
    # =========================================================================
    section("2️⃣  IMPACT FACTOR - Assess Journal Quality")

    print("  Calculate real impact factors from citation data.\n")

    try:
        from crossref_local.impact_factor import ImpactFactorCalculator

        journals = [
            ("Nature", "Top multidisciplinary"),
            ("Science", "Top multidisciplinary"),
            ("Cell", "Top biology"),
            ("PLOS ONE", "Open access"),
        ]

        with ImpactFactorCalculator() as calc:
            print(f"  {'Journal':<20} {'Category':<25} {'IF 2023':>10}")
            print(f"  {'-'*57}")

            for journal, category in journals:
                try:
                    result = calc.calculate_impact_factor(journal, target_year=2023)
                    if_val = result.get('impact_factor', 0) if result else 0
                    print(f"  {journal:<20} {category:<25} {if_val:>10.2f}")
                except:
                    print(f"  {journal:<20} {category:<25} {'N/A':>10}")

        print("\n  → Filter papers by journal quality for better LLM context!\n")

    except Exception as e:
        print(f"  Impact factor calculation: {e}\n")

    # =========================================================================
    # 3. CITATION METRICS - Paper Importance
    # =========================================================================
    section("3️⃣  CITATIONS - Measure Paper Importance")

    print("  Citation data helps LLMs prioritize influential papers.\n")

    # Show works with citation potential
    high_impact_query = "deep learning transformer attention"
    results = search(high_impact_query, limit=3)

    print(f"  Query: '{high_impact_query}'\n")

    for i, work in enumerate(results.works, 1):
        print(f"  [{i}] {work.title[:55]}...")
        print(f"      {work.year} | DOI: {work.doi}")
        # Note: citation count would come from citations table
        print()

    print("  → Prioritize highly-cited papers in LLM prompts!\n")

    # =========================================================================
    # 4. SPEED - No Rate Limits
    # =========================================================================
    section("4️⃣  SPEED - 167M Records, No Rate Limits")

    print("  Process thousands of papers without API throttling.\n")

    queries = [
        "machine learning",
        "CRISPR cas9",
        "climate model",
        "neural network",
        "protein folding",
    ]

    total_time = 0
    total_matches = 0

    print(f"  {'Query':<30} {'Matches':>12} {'Time':>10}")
    print(f"  {'-'*54}")

    for q in queries:
        start = time.perf_counter()
        n = count(q)
        elapsed = (time.perf_counter() - start) * 1000
        total_time += elapsed
        total_matches += n
        print(f"  {q:<30} {n:>12,} {elapsed:>8.0f}ms")

    print(f"  {'-'*54}")
    print(f"  {'TOTAL':<30} {total_matches:>12,} {total_time:>8.0f}ms")

    print(f"\n  → {total_matches:,} papers indexed in {total_time:.0f}ms!")
    print("  → Online API would need minutes + hit rate limits\n")

    # =========================================================================
    # Summary
    # =========================================================================
    print("━"*70)
    print("  🚀 WHY CROSSREF LOCAL FOR LLM APPLICATIONS?")
    print("━"*70)
    print("""
  ┌─────────────────────────────────────────────────────────────────┐
  │                                                                 │
  │  📝 ABSTRACTS      Full text for semantic understanding        │
  │  📊 IMPACT FACTOR  Filter by journal quality                   │
  │  🔗 CITATIONS      Prioritize influential papers               │
  │  ⚡ SPEED          No rate limits, instant results             │
  │                                                                 │
  │  Perfect for: RAG systems, research assistants, paper          │
  │  recommendation, literature review automation                  │
  │                                                                 │
  └─────────────────────────────────────────────────────────────────┘
""")


if __name__ == "__main__":
    demo()
