#!/usr/bin/env python3
"""
Rebuild citations table with complete year-specific citation data.

This script extracts all citation relationships from the works table
and populates the citations table with (citing_doi, cited_doi, citing_year).

Features:
- Batch processing for memory efficiency
- Progress tracking with ETA
- Checkpoint/resume capability
- Transaction-based for consistency
- Handles malformed JSON gracefully
"""

import sqlite3
import json
import logging
import time
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"rebuild_citations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CitationsTableBuilder:
    """Build citations table from works table."""

    def __init__(self, db_path: str, batch_size: int = 1000):
        """
        Initialize builder.

        Args:
            db_path: Path to CrossRef database
            batch_size: Number of papers to process per batch
        """
        self.db_path = Path(db_path)
        if not self.db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        self.batch_size = batch_size
        self.conn = None
        self.checkpoint_file = Path("citations_rebuild_checkpoint.txt")
        self.checkpoint_file_v2 = Path("citations_rebuild_checkpoint_v2.txt")  # id-based

        # Statistics
        self.total_papers = 0
        self.papers_processed = 0
        self.citations_inserted = 0
        self.papers_with_refs = 0
        self.errors = 0
        self.start_time = None
        self.last_checkpoint = None

    def connect(self, timeout: float = 30.0):
        """Connect to database with timeout.

        Args:
            timeout: Connection timeout in seconds (default: 30)
        """
        self.conn = sqlite3.connect(self.db_path, timeout=timeout)
        self.conn.row_factory = sqlite3.Row
        # Set pragmas for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        self.conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
        logger.info(f"Connected to database: {self.db_path}")

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def check_database_lock(self) -> bool:
        """
        Check if database is locked by attempting a brief exclusive lock.

        Returns:
            True if database is accessible, False if locked
        """
        try:
            # Try to begin an immediate transaction (fails if locked)
            self.conn.execute("BEGIN IMMEDIATE")
            self.conn.execute("ROLLBACK")
            return True
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower():
                logger.error(f"Database is locked: {e}")
                logger.error("\nPossible causes:")
                logger.error("  1. Another Python script is accessing the database")
                logger.error("  2. SQLite browser or DB tool is open")
                logger.error("  3. Stale connection from previous session")
                logger.error("\nTo fix:")
                logger.error("  - Close all programs accessing the database")
                logger.error("  - Check for processes: lsof /path/to/crossref.db")
                logger.error("  - Kill stale processes: ps aux | grep crossref")
                return False
            raise

    def get_total_papers(self) -> int:
        """Get total number of papers to process."""
        query = "SELECT COUNT(*) FROM works WHERE json_extract(metadata, '$.reference') IS NOT NULL"
        cursor = self.conn.execute(query)
        return cursor.fetchone()[0]

    def load_checkpoint(self) -> Optional[int]:
        """
        Load last processed paper id from checkpoint file.

        Returns:
            Last processed id to resume from, or None to start from beginning
        """
        # Try v2 (id-based) checkpoint first
        if self.checkpoint_file_v2.exists():
            try:
                with open(self.checkpoint_file_v2, 'r') as f:
                    last_id = int(f.read().strip())
                logger.info(f"Resuming from checkpoint v2: last_id {last_id:,}")
                return last_id
            except Exception as e:
                logger.warning(f"Could not load v2 checkpoint: {e}")

        # Fall back to v1 (offset-based) and migrate
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    offset = int(f.read().strip())
                logger.info(f"Found v1 checkpoint with offset {offset:,}, migrating to id-based...")
                # Convert offset to id by finding the id at that position
                last_id = self.convert_offset_to_id(offset)
                if last_id:
                    logger.info(f"Migrated to id-based checkpoint: last_id {last_id:,}")
                    self.save_checkpoint(last_id)
                    return last_id
            except Exception as e:
                logger.warning(f"Could not load/migrate v1 checkpoint: {e}")
        return None

    def convert_offset_to_id(self, offset: int) -> Optional[int]:
        """
        Convert old offset-based checkpoint to id-based.

        Uses a smart approach: find the last work id that has citations in our table.
        This is much faster than using OFFSET on 21M+ rows.

        Args:
            offset: The offset from old checkpoint (used for verification)

        Returns:
            The id of the last processed paper
        """
        logger.info(f"Converting offset {offset:,} to id using citations data...")

        # Smart approach: find the max work id that has citations in our table
        # This gives us the last processed work directly from existing data
        query = """
            SELECT MAX(w.id) FROM works w
            WHERE w.doi IN (SELECT DISTINCT citing_doi FROM citations)
        """
        cursor = self.conn.execute(query)
        row = cursor.fetchone()

        if row and row[0]:
            last_id = row[0]
            logger.info(f"Found last processed work id from citations: {last_id:,}")
            return last_id

        # Fallback: estimate based on ratio of papers with references
        # This is O(1) instead of O(n)
        logger.info("Fallback: estimating id from offset...")
        cursor = self.conn.execute("SELECT COUNT(*) FROM works")
        total_works = cursor.fetchone()[0]

        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM works WHERE json_extract(metadata, '$.reference') IS NOT NULL"
        )
        papers_with_refs = cursor.fetchone()[0]

        # Estimate: offset / papers_with_refs * total_works
        if papers_with_refs > 0:
            ratio = total_works / papers_with_refs
            estimated_id = int(offset * ratio)
            logger.info(f"Estimated id from offset: {estimated_id:,} (ratio: {ratio:.2f})")
            return estimated_id

        return None

    def save_checkpoint(self, last_id: int):
        """Save current progress to checkpoint file (id-based)."""
        with open(self.checkpoint_file_v2, 'w') as f:
            f.write(str(last_id))
        self.last_checkpoint = last_id

    def delete_checkpoint(self):
        """Delete checkpoint files after successful completion."""
        for f in [self.checkpoint_file, self.checkpoint_file_v2]:
            if f.exists():
                f.unlink()
        logger.info("Checkpoint files deleted")

    def backup_existing_table(self, max_retries: int = 3):
        """Backup existing citations table with retry logic.

        Args:
            max_retries: Maximum number of retry attempts (default: 3)
        """
        logger.info("Checking for existing citations table...")
        cursor = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='citations'"
        )
        if cursor.fetchone():
            backup_name = f"citations_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"Backing up existing citations table to {backup_name}...")

            # Retry logic for handling transient locks
            for attempt in range(max_retries):
                try:
                    self.conn.execute(f"ALTER TABLE citations RENAME TO {backup_name}")
                    self.conn.commit()
                    logger.info(f"Backup created: {backup_name}")
                    return
                except sqlite3.OperationalError as e:
                    if "locked" in str(e).lower() and attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                        logger.warning(f"Database locked, retrying in {wait_time}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                    else:
                        logger.error(f"Failed to backup table after {max_retries} attempts")
                        raise

    def create_citations_table(self):
        """Create citations table with proper schema."""
        logger.info("Creating citations table...")

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS citations (
                citing_doi TEXT NOT NULL,
                cited_doi TEXT NOT NULL,
                citing_year INTEGER NOT NULL,
                PRIMARY KEY (citing_doi, cited_doi)
            )
        """)
        self.conn.commit()
        logger.info("Citations table created")

    def create_indices(self):
        """Create indices on citations table."""
        logger.info("Creating indices on citations table...")

        indices = [
            ("idx_citations_cited", "CREATE INDEX idx_citations_cited ON citations(cited_doi, citing_year)"),
            ("idx_citations_citing", "CREATE INDEX idx_citations_citing ON citations(citing_doi)"),
            ("idx_citations_year", "CREATE INDEX idx_citations_year ON citations(citing_year)")
        ]

        for idx_name, idx_sql in indices:
            logger.info(f"  Creating {idx_name}...")
            try:
                self.conn.execute(idx_sql)
            except sqlite3.OperationalError as e:
                if "already exists" in str(e):
                    logger.info(f"  {idx_name} already exists, skipping")
                else:
                    raise

        self.conn.commit()
        logger.info("Indices created")

    def extract_citations_from_paper(self, row: sqlite3.Row) -> List[Tuple[str, str, int]]:
        """
        Extract citation relationships from a single paper.

        Args:
            row: Database row with doi and metadata

        Returns:
            List of (citing_doi, cited_doi, citing_year) tuples
        """
        try:
            citing_doi = row['doi']
            if not citing_doi:
                return []

            # Parse metadata JSON
            metadata = json.loads(row['metadata'])

            # Get publication year
            date_parts = metadata.get('published', {}).get('date-parts', [[]])
            if not date_parts or not date_parts[0]:
                return []

            citing_year = date_parts[0][0]
            if not citing_year or not isinstance(citing_year, int):
                return []

            # Get references
            references = metadata.get('reference', [])
            if not references or not isinstance(references, list):
                return []

            # Extract citation tuples
            citations = []
            for ref in references:
                if not isinstance(ref, dict):
                    continue

                cited_doi = ref.get('DOI', '').strip()
                if cited_doi:
                    citations.append((citing_doi, cited_doi, citing_year))

            return citations

        except json.JSONDecodeError as e:
            logger.debug(f"JSON decode error for DOI {row.get('doi', 'unknown')}: {e}")
            self.errors += 1
            return []
        except Exception as e:
            logger.debug(f"Error processing DOI {row.get('doi', 'unknown')}: {e}")
            self.errors += 1
            return []

    def process_batch(self, last_id: int) -> Tuple[int, int]:
        """
        Process a batch of papers using cursor-based pagination.

        Args:
            last_id: Last processed paper id (process papers with id > last_id)

        Returns:
            Tuple of (citations_inserted, new_last_id)
        """
        # Query batch of papers with references using cursor-based pagination
        # This is O(log n) instead of O(n) for OFFSET-based queries
        query = """
            SELECT id, doi, metadata
            FROM works
            WHERE id > ? AND json_extract(metadata, '$.reference') IS NOT NULL
            ORDER BY id
            LIMIT ?
        """

        cursor = self.conn.execute(query, (last_id, self.batch_size))
        rows = cursor.fetchall()

        if not rows:
            return 0, last_id

        # Extract all citations from this batch
        all_citations = []
        papers_in_batch = len(rows)
        new_last_id = last_id

        for row in rows:
            new_last_id = row['id']  # Track the last processed id
            citations = self.extract_citations_from_paper(row)
            if citations:
                all_citations.extend(citations)
                self.papers_with_refs += 1

        # Insert citations in a transaction
        if all_citations:
            try:
                self.conn.executemany(
                    "INSERT OR IGNORE INTO citations (citing_doi, cited_doi, citing_year) VALUES (?, ?, ?)",
                    all_citations
                )
                self.conn.commit()
            except Exception as e:
                logger.error(f"Error inserting batch after id {last_id}: {e}")
                self.conn.rollback()
                raise

        citations_inserted = len(all_citations)
        self.citations_inserted += citations_inserted
        self.papers_processed += papers_in_batch

        return citations_inserted, new_last_id

    def log_progress(self, elapsed: float):
        """Log current progress with ETA."""
        if self.total_papers == 0:
            return

        progress_pct = (self.papers_processed / self.total_papers) * 100
        papers_per_sec = self.papers_processed / elapsed if elapsed > 0 else 0

        # Calculate ETA
        remaining_papers = self.total_papers - self.papers_processed
        eta_seconds = remaining_papers / papers_per_sec if papers_per_sec > 0 else 0
        eta_str = str(timedelta(seconds=int(eta_seconds)))

        logger.info(
            f"Progress: {self.papers_processed:,}/{self.total_papers:,} papers "
            f"({progress_pct:.1f}%) | "
            f"{self.citations_inserted:,} citations | "
            f"{papers_per_sec:.1f} papers/sec | "
            f"ETA: {eta_str}"
        )

    def rebuild(self, resume: bool = True, skip_backup: bool = False):
        """
        Rebuild citations table.

        Args:
            resume: If True, resume from checkpoint
            skip_backup: If True, skip backing up existing table
        """
        self.start_time = time.time()

        # Check for database locks before starting
        logger.info("Checking database accessibility...")
        if not self.check_database_lock():
            raise RuntimeError("Database is locked. Please close all programs accessing it and try again.")

        # Get total papers to process
        logger.info("Counting papers with references...")
        self.total_papers = self.get_total_papers()
        logger.info(f"Total papers to process: {self.total_papers:,}")

        # Get max id for progress tracking
        cursor = self.conn.execute("SELECT MAX(id) FROM works")
        max_id = cursor.fetchone()[0] or 0
        logger.info(f"Max work id: {max_id:,}")

        # Check for resume
        last_id = 0
        papers_already_processed = 0
        if resume:
            checkpoint_id = self.load_checkpoint()
            if checkpoint_id:
                last_id = checkpoint_id
                # Count how many papers we've already processed
                cursor = self.conn.execute(
                    "SELECT COUNT(*) FROM works WHERE id <= ? AND json_extract(metadata, '$.reference') IS NOT NULL",
                    (last_id,)
                )
                papers_already_processed = cursor.fetchone()[0]
                self.papers_processed = papers_already_processed
                # Get current citation count
                cursor = self.conn.execute("SELECT COUNT(*) FROM citations")
                self.citations_inserted = cursor.fetchone()[0]
                logger.info(f"Resuming from id {last_id:,} ({papers_already_processed:,} papers already processed)")
                logger.info(f"Existing citations in table: {self.citations_inserted:,}")
            else:
                # New run - backup and recreate table
                if not skip_backup:
                    self.backup_existing_table()
                self.create_citations_table()
        else:
            # Fresh start
            if not skip_backup:
                self.backup_existing_table()
            self.create_citations_table()

        # Process all papers in batches
        logger.info(f"Processing papers in batches of {self.batch_size:,}...")

        checkpoint_interval = 10000  # Save checkpoint every 10k papers
        last_log_time = time.time()
        log_interval = 10  # Log every 10 seconds
        last_checkpoint_papers = self.papers_processed

        try:
            while True:
                # Process batch using cursor-based pagination
                citations_count, new_last_id = self.process_batch(last_id)

                # Check if we're done (no more papers to process)
                if new_last_id == last_id:
                    break

                last_id = new_last_id

                # Save checkpoint periodically
                if self.papers_processed - last_checkpoint_papers >= checkpoint_interval:
                    self.save_checkpoint(last_id)
                    last_checkpoint_papers = self.papers_processed

                # Log progress periodically
                current_time = time.time()
                if current_time - last_log_time >= log_interval:
                    self.log_progress(current_time - self.start_time)
                    last_log_time = current_time

                # Break if we've processed all papers
                if self.papers_processed >= self.total_papers:
                    break

        except KeyboardInterrupt:
            logger.warning("\nInterrupted by user. Saving checkpoint...")
            self.save_checkpoint(last_id)
            raise
        except Exception as e:
            logger.error(f"Error during rebuild: {e}")
            self.save_checkpoint(last_id)
            raise

        # Create indices
        logger.info("\nCreating indices (this may take a while)...")
        self.create_indices()

        # Clean up checkpoint
        self.delete_checkpoint()

        # Final statistics
        elapsed = time.time() - self.start_time
        self.log_final_statistics(elapsed)

    def log_final_statistics(self, elapsed: float):
        """Log final statistics."""
        logger.info("\n" + "="*70)
        logger.info("REBUILD COMPLETE")
        logger.info("="*70)
        logger.info(f"Total papers processed: {self.papers_processed:,}")
        logger.info(f"Papers with references: {self.papers_with_refs:,}")
        logger.info(f"Total citations inserted: {self.citations_inserted:,}")
        logger.info(f"Errors encountered: {self.errors:,}")
        logger.info(f"Time elapsed: {timedelta(seconds=int(elapsed))}")
        logger.info(f"Processing rate: {self.papers_processed/elapsed:.1f} papers/sec")
        logger.info("="*70)

        # Verify final table
        cursor = self.conn.execute("SELECT COUNT(*) FROM citations")
        final_count = cursor.fetchone()[0]
        logger.info(f"Final citations table size: {final_count:,} rows")

        # Year distribution
        logger.info("\nCitation year distribution:")
        cursor = self.conn.execute("""
            SELECT citing_year, COUNT(*) as count
            FROM citations
            GROUP BY citing_year
            ORDER BY citing_year DESC
            LIMIT 10
        """)
        for row in cursor:
            logger.info(f"  {row[0]}: {row[1]:,} citations")


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild citations table with complete year-specific data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fresh rebuild (backs up existing table)
  python rebuild_citations_table.py --db /path/to/crossref.db

  # Resume from checkpoint
  python rebuild_citations_table.py --db /path/to/crossref.db --resume

  # Fresh rebuild without backup
  python rebuild_citations_table.py --db /path/to/crossref.db --no-backup

  # Custom batch size
  python rebuild_citations_table.py --db /path/to/crossref.db --batch-size 5000
        """
    )

    parser.add_argument(
        "--db",
        type=str,
        default="./data/crossref.db",
        help="Path to CrossRef database"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of papers to process per batch (default: 1000)"
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last checkpoint"
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip backing up existing citations table"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("="*70)
    logger.info("CITATIONS TABLE REBUILD SCRIPT")
    logger.info("="*70)
    logger.info(f"Database: {args.db}")
    logger.info(f"Batch size: {args.batch_size:,}")
    logger.info(f"Resume: {args.resume}")
    logger.info(f"Backup existing: {not args.no_backup}")
    logger.info("="*70)

    try:
        with CitationsTableBuilder(args.db, args.batch_size) as builder:
            builder.rebuild(resume=args.resume, skip_backup=args.no_backup)

        logger.info("\n✓ Rebuild completed successfully!")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n✗ Interrupted by user. Progress saved to checkpoint.")
        logger.info("Run with --resume to continue from last checkpoint.")
        return 1
    except Exception as e:
        logger.error(f"\n✗ Rebuild failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
