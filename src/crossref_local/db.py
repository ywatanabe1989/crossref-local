"""Database connection handling for crossref_local."""

import sqlite3
import json
import zlib
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Generator

from .config import Config


class Database:
    """
    Database connection manager.

    Supports both direct usage and context manager pattern.
    """

    def __init__(self, db_path: Optional[str | Path] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to database. If None, auto-detects.
        """
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = Config.get_db_path()

        self.conn: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self) -> None:
        """Establish database connection."""
        # check_same_thread=False allows connection to be used across threads
        # Safe for read-only operations (which is our use case)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL query."""
        return self.conn.execute(query, params)

    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute query and fetch one result."""
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def fetchall(self, query: str, params: tuple = ()) -> list:
        """Execute query and fetch all results."""
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def get_metadata(self, doi: str) -> Optional[dict]:
        """
        Get metadata for a DOI.

        Args:
            doi: DOI string

        Returns:
            Metadata dictionary or None
        """
        row = self.fetchone(
            "SELECT metadata FROM works WHERE doi = ?",
            (doi,)
        )
        if row and row["metadata"]:
            return self._decompress_metadata(row["metadata"])
        return None

    def _decompress_metadata(self, data) -> dict:
        """Decompress and parse metadata (handles both compressed and plain JSON)."""
        # If it's already a string, parse directly
        if isinstance(data, str):
            return json.loads(data)

        # If bytes, try decompression
        if isinstance(data, bytes):
            try:
                decompressed = zlib.decompress(data)
                return json.loads(decompressed)
            except zlib.error:
                return json.loads(data.decode("utf-8"))

        return data


# Singleton connection for convenience functions
_db: Optional[Database] = None


def get_db() -> Database:
    """Get or create singleton database connection."""
    global _db
    if _db is None:
        _db = Database()
    return _db


def close_db() -> None:
    """Close singleton database connection."""
    global _db
    if _db:
        _db.close()
        _db = None


@contextmanager
def connection(db_path: Optional[str | Path] = None) -> Generator[Database, None, None]:
    """
    Context manager for database connection.

    Args:
        db_path: Path to database. If None, auto-detects.

    Yields:
        Database instance
    """
    db = Database(db_path)
    try:
        yield db
    finally:
        db.close()
