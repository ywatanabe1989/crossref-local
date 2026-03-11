"""Database connection handling for crossref_local."""

import json as _json
import sqlite3 as _sqlite3
import zlib as _zlib
from contextlib import contextmanager as _contextmanager
from pathlib import Path as _Path
from typing import Generator, Optional

from .config import Config as _Config

__all__ = [
    "Database",
    "get_db",
    "close_db",
    "connection",
]


class Database:
    """
    Database connection manager.

    Supports both direct usage and context manager pattern.
    """

    def __init__(self, db_path: Optional[str | _Path] = None):
        """
        Initialize database connection.

        Args:
            db_path: Path to database. If None, auto-detects.
        """
        if db_path:
            self.db_path = _Path(db_path)
        else:
            self.db_path = _Config.get_db_path()

        self.conn: Optional[_sqlite3.Connection] = None
        self._connect()

    def _connect(self) -> None:
        """Establish database connection."""
        # check_same_thread=False allows connection to be used across threads
        # Safe for read-only operations (which is our use case)
        self.conn = _sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = _sqlite3.Row

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def execute(self, query: str, params: tuple = ()) -> _sqlite3.Cursor:
        """Execute SQL query."""
        return self.conn.execute(query, params)

    def fetchone(self, query: str, params: tuple = ()) -> Optional[_sqlite3.Row]:
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
        row = self.fetchone("SELECT metadata FROM works WHERE doi = ?", (doi,))
        if row and row["metadata"]:
            return self._decompress_metadata(row["metadata"])
        return None

    def _decompress_metadata(self, data) -> dict:
        """Decompress and parse metadata (handles both compressed and plain JSON)."""
        # If it's already a string, parse directly
        if isinstance(data, str):
            return _json.loads(data)

        # If bytes, try decompression
        if isinstance(data, bytes):
            try:
                decompressed = _zlib.decompress(data)
                return _json.loads(decompressed)
            except _zlib.error:
                return _json.loads(data.decode("utf-8"))

        return data


# Thread-local storage for database connections (SQLite is not thread-safe)
import threading as _threading

_local = _threading.local()


def get_db() -> Database:
    """Get or create thread-local database connection.

    Each thread gets its own Database instance to avoid SQLite threading errors.
    SQLite connections cannot be safely shared across threads.
    """
    if not hasattr(_local, 'db') or _local.db is None:
        _local.db = Database()
    return _local.db


def close_db() -> None:
    """Close thread-local database connection."""
    if hasattr(_local, 'db') and _local.db:
        _local.db.close()
        _local.db = None


@_contextmanager
def connection(
    db_path: Optional[str | _Path] = None,
) -> Generator[Database, None, None]:
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
