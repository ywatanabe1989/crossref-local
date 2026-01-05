#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-10-12 03:01:00 (ywatanabe)"
# File: /mnt/nas_ug/crossref_local/impact_factor/analyze_journals.py

"""
Analyze journals in CrossRef database.

Features:
- Find unique journals
- Calculate average citation count per paper
- Group by year
- Export statistics to CSV
"""

import argparse
import csv
import json
import logging
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class JournalAnalyzer:
    """Analyze journal statistics from CrossRef database."""

    def __init__(self, db_path: str = "/mnt/nas_ug/crossref_local/data/crossref.db"):
        """Initialize analyzer with database connection."""
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def find_unique_journals(
        self,
        limit: Optional[int] = None,
        min_articles: int = 1
    ) -> List[Dict]:
        """
        Find unique journals in database.

        Args:
            limit: Maximum number of journals to return
            min_articles: Minimum number of articles for inclusion

        Returns:
            List of journal dictionaries with metadata
        """
        logger.info("Finding unique journals...")

        query = """
        SELECT
            json_extract(metadata, '$.container-title[0]') as journal,
            json_extract(metadata, '$.ISSN[0]') as issn,
            json_extract(metadata, '$.publisher') as publisher,
            COUNT(*) as article_count
        FROM works
        WHERE json_extract(metadata, '$.type') = 'journal-article'
        AND journal IS NOT NULL
        GROUP BY journal, issn
        HAVING article_count >= ?
        ORDER BY article_count DESC
        """

        if limit:
            query += f" LIMIT {limit}"

        cursor = self.conn.execute(query, (min_articles,))

        journals = []
        for row in cursor:
            journals.append({
                'journal': row['journal'],
                'issn': row['issn'],
                'publisher': row['publisher'],
                'article_count': row['article_count']
            })

        logger.info(f"Found {len(journals)} unique journals")
        return journals

    def calculate_citation_stats_by_year(
        self,
        journal_name: Optional[str] = None,
        issn: Optional[str] = None,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None
    ) -> List[Dict]:
        """
        Calculate average citation count per paper by year.

        Args:
            journal_name: Journal name (optional)
            issn: Journal ISSN (optional)
            start_year: Start year for analysis
            end_year: End year for analysis

        Returns:
            List of statistics by year
        """
        logger.info(f"Calculating citation statistics...")

        # Build query
        query = """
        SELECT
            json_extract(metadata, '$.container-title[0]') as journal,
            json_extract(metadata, '$.ISSN[0]') as issn,
            json_extract(metadata, '$.published.date-parts[0][0]') as year,
            CAST(json_extract(metadata, '$.is-referenced-by-count') AS INTEGER) as citations,
            doi
        FROM works
        WHERE json_extract(metadata, '$.type') = 'journal-article'
        """

        params = []

        if journal_name:
            query += " AND journal LIKE ?"
            params.append(f"%{journal_name}%")

        if issn:
            query += " AND issn = ?"
            params.append(issn)

        if start_year:
            query += " AND year >= ?"
            params.append(start_year)

        if end_year:
            query += " AND year <= ?"
            params.append(end_year)

        query += " AND year IS NOT NULL"

        cursor = self.conn.execute(query, params)

        # Collect data by year
        data_by_year = defaultdict(list)
        journal_info = None

        for row in cursor:
            year = row['year']
            citations = row['citations'] if row['citations'] is not None else 0
            data_by_year[year].append(citations)

            if journal_info is None:
                journal_info = {
                    'journal': row['journal'],
                    'issn': row['issn']
                }

        # Calculate statistics
        results = []
        for year in sorted(data_by_year.keys()):
            citations = data_by_year[year]

            stats = {
                'year': year,
                'journal': journal_info['journal'] if journal_info else 'All journals',
                'issn': journal_info['issn'] if journal_info else None,
                'article_count': len(citations),
                'total_citations': sum(citations),
                'avg_citations': np.mean(citations),
                'median_citations': np.median(citations),
                'std_citations': np.std(citations),
                'min_citations': min(citations),
                'max_citations': max(citations),
                'q25_citations': np.percentile(citations, 25),
                'q75_citations': np.percentile(citations, 75),
            }

            results.append(stats)

        logger.info(f"Calculated statistics for {len(results)} years")
        return results

    def calculate_citation_stats_all_journals(
        self,
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        min_articles: int = 100,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Calculate citation statistics for all journals.

        Args:
            start_year: Start year
            end_year: End year
            min_articles: Minimum articles for inclusion
            limit: Maximum number of journals

        Returns:
            List of journal statistics
        """
        logger.info("Calculating statistics for all journals...")

        # First, get list of journals
        journals = self.find_unique_journals(limit=limit, min_articles=min_articles)

        all_stats = []

        for i, journal_info in enumerate(journals):
            logger.info(f"Processing {i+1}/{len(journals)}: {journal_info['journal']}")

            stats = self.calculate_citation_stats_by_year(
                issn=journal_info['issn'],
                start_year=start_year,
                end_year=end_year
            )

            # Aggregate across years
            if stats:
                all_articles = sum(s['article_count'] for s in stats)
                all_citations = sum(s['total_citations'] for s in stats)
                avg_citations = all_citations / all_articles if all_articles > 0 else 0

                all_stats.append({
                    'journal': journal_info['journal'],
                    'issn': journal_info['issn'],
                    'publisher': journal_info['publisher'],
                    'total_articles': all_articles,
                    'total_citations': all_citations,
                    'avg_citations_per_paper': avg_citations,
                    'years_active': len(stats),
                    'first_year': min(s['year'] for s in stats),
                    'last_year': max(s['year'] for s in stats)
                })

        logger.info(f"Processed {len(all_stats)} journals")
        return all_stats

    def get_database_stats(self) -> Dict:
        """Get overall database statistics."""
        logger.info("Getting database statistics...")

        stats = {}

        # Total articles
        cursor = self.conn.execute(
            "SELECT COUNT(*) as count FROM works WHERE json_extract(metadata, '$.type') = 'journal-article'"
        )
        stats['total_articles'] = cursor.fetchone()['count']

        # Unique journals
        cursor = self.conn.execute(
            "SELECT COUNT(DISTINCT json_extract(metadata, '$.container-title[0]')) as count FROM works WHERE json_extract(metadata, '$.type') = 'journal-article'"
        )
        stats['unique_journals'] = cursor.fetchone()['count']

        # Year range
        cursor = self.conn.execute(
            """
            SELECT
                MIN(CAST(json_extract(metadata, '$.published.date-parts[0][0]') AS INTEGER)) as min_year,
                MAX(CAST(json_extract(metadata, '$.published.date-parts[0][0]') AS INTEGER)) as max_year
            FROM works
            WHERE json_extract(metadata, '$.type') = 'journal-article'
            """
        )
        row = cursor.fetchone()
        stats['year_range'] = f"{row['min_year']}-{row['max_year']}"

        return stats


def write_csv(data: List[Dict], output_path: str, mode: str = 'journals'):
    """Write results to CSV file."""
    if not data:
        logger.warning("No data to write")
        return

    with open(output_path, 'w', newline='') as f:
        if mode == 'journals':
            fieldnames = [
                'journal', 'issn', 'publisher', 'total_articles',
                'total_citations', 'avg_citations_per_paper',
                'years_active', 'first_year', 'last_year'
            ]
        elif mode == 'by_year':
            fieldnames = [
                'year', 'journal', 'issn', 'article_count',
                'total_citations', 'avg_citations', 'median_citations',
                'std_citations', 'min_citations', 'max_citations',
                'q25_citations', 'q75_citations'
            ]
        else:
            fieldnames = list(data[0].keys())

        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data)

    logger.info(f"Results written to {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Analyze journals and citation statistics in CrossRef database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all unique journals
  %(prog)s --list-journals --output journals.csv

  # List top 100 journals by article count
  %(prog)s --list-journals --limit 100 --min-articles 1000

  # Calculate citation stats for a specific journal
  %(prog)s --journal "Nature" --by-year --output nature_stats.csv

  # Calculate stats for all major journals
  %(prog)s --all-journals --min-articles 1000 --limit 50 --output top50.csv

  # Analyze specific year range
  %(prog)s --journal "Science" --start-year 2018 --end-year 2024 --by-year

  # Get database statistics
  %(prog)s --db-stats
        """
    )

    # Mode selection
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--list-journals',
        action='store_true',
        help='List unique journals'
    )
    mode_group.add_argument(
        '--journal',
        type=str,
        help='Analyze specific journal'
    )
    mode_group.add_argument(
        '--issn',
        type=str,
        help='Analyze journal by ISSN'
    )
    mode_group.add_argument(
        '--all-journals',
        action='store_true',
        help='Analyze all journals'
    )
    mode_group.add_argument(
        '--db-stats',
        action='store_true',
        help='Show database statistics'
    )

    # Filters
    parser.add_argument(
        '--start-year',
        type=int,
        help='Start year for analysis'
    )
    parser.add_argument(
        '--end-year',
        type=int,
        help='End year for analysis'
    )
    parser.add_argument(
        '--min-articles',
        type=int,
        default=1,
        help='Minimum number of articles (default: 1)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Maximum number of journals to process'
    )

    # Analysis options
    parser.add_argument(
        '--by-year',
        action='store_true',
        help='Group statistics by year'
    )

    # Database
    parser.add_argument(
        '--db',
        type=str,
        default='/mnt/nas_ug/crossref_local/data/crossref.db',
        help='Path to CrossRef database'
    )

    # Output
    parser.add_argument(
        '--output',
        type=str,
        help='Output CSV file'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    with JournalAnalyzer(db_path=args.db) as analyzer:
        if args.db_stats:
            # Show database statistics
            stats = analyzer.get_database_stats()
            print("\n" + "="*70)
            print("Database Statistics")
            print("="*70)
            for key, value in stats.items():
                print(f"{key.replace('_', ' ').title()}: {value:,}" if isinstance(value, int) else f"{key.replace('_', ' ').title()}: {value}")
            print("="*70 + "\n")

        elif args.list_journals:
            # List unique journals
            journals = analyzer.find_unique_journals(
                limit=args.limit,
                min_articles=args.min_articles
            )

            if args.output:
                write_csv(journals, args.output, mode='journals')
            else:
                print("\n" + "="*70)
                print(f"Found {len(journals)} journals")
                print("="*70)
                for i, journal in enumerate(journals[:20], 1):
                    print(f"{i}. {journal['journal']}")
                    print(f"   ISSN: {journal['issn']}")
                    print(f"   Articles: {journal['article_count']:,}")
                    print()
                if len(journals) > 20:
                    print(f"... and {len(journals) - 20} more journals")
                print("="*70 + "\n")

        elif args.journal or args.issn:
            # Analyze specific journal
            if args.by_year:
                stats = analyzer.calculate_citation_stats_by_year(
                    journal_name=args.journal,
                    issn=args.issn,
                    start_year=args.start_year,
                    end_year=args.end_year
                )

                if args.output:
                    write_csv(stats, args.output, mode='by_year')
                else:
                    print("\n" + "="*70)
                    print(f"Citation Statistics by Year")
                    print("="*70)
                    for stat in stats:
                        print(f"{stat['year']}: {stat['article_count']:,} articles, "
                              f"avg {stat['avg_citations']:.2f} citations/paper")
                    print("="*70 + "\n")
            else:
                stats = analyzer.calculate_citation_stats_by_year(
                    journal_name=args.journal,
                    issn=args.issn,
                    start_year=args.start_year,
                    end_year=args.end_year
                )

                # Aggregate across years
                if stats:
                    total_articles = sum(s['article_count'] for s in stats)
                    total_citations = sum(s['total_citations'] for s in stats)
                    avg_citations = total_citations / total_articles if total_articles > 0 else 0

                    print("\n" + "="*70)
                    print(f"Overall Statistics")
                    print("="*70)
                    print(f"Journal: {stats[0]['journal']}")
                    print(f"ISSN: {stats[0]['issn']}")
                    print(f"Total articles: {total_articles:,}")
                    print(f"Total citations: {total_citations:,}")
                    print(f"Average citations per paper: {avg_citations:.2f}")
                    print(f"Years: {min(s['year'] for s in stats)}-{max(s['year'] for s in stats)}")
                    print("="*70 + "\n")

        elif args.all_journals:
            # Analyze all journals
            stats = analyzer.calculate_citation_stats_all_journals(
                start_year=args.start_year,
                end_year=args.end_year,
                min_articles=args.min_articles,
                limit=args.limit
            )

            if args.output:
                write_csv(stats, args.output, mode='journals')
            else:
                print("\n" + "="*70)
                print(f"Top Journals by Citation Count")
                print("="*70)
                sorted_stats = sorted(stats, key=lambda x: x['avg_citations_per_paper'], reverse=True)
                for i, stat in enumerate(sorted_stats[:20], 1):
                    print(f"{i}. {stat['journal']}")
                    print(f"   Articles: {stat['total_articles']:,}")
                    print(f"   Avg citations/paper: {stat['avg_citations_per_paper']:.2f}")
                    print()
                if len(sorted_stats) > 20:
                    print(f"... and {len(sorted_stats) - 20} more journals")
                print("="*70 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())

# EOF
