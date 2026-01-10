"""Configuration for crossref_local."""

import os
from pathlib import Path
from typing import Optional

# Default database locations (checked in order)
DEFAULT_DB_PATHS = [
    Path("/home/ywatanabe/proj/crossref_local/data/crossref.db"),
    Path("/mnt/nas_ug/crossref_local/data/crossref.db"),
    Path.home() / ".crossref_local" / "crossref.db",
    Path.cwd() / "data" / "crossref.db",
]


def get_db_path() -> Path:
    """
    Get database path from environment or auto-detect.

    Priority:
    1. CROSSREF_LOCAL_DB environment variable
    2. First existing path from DEFAULT_DB_PATHS

    Returns:
        Path to the database file

    Raises:
        FileNotFoundError: If no database found
    """
    # Check environment variable first
    env_path = os.environ.get("CROSSREF_LOCAL_DB")
    if env_path:
        path = Path(env_path)
        if path.exists():
            return path
        raise FileNotFoundError(f"CROSSREF_LOCAL_DB path not found: {env_path}")

    # Auto-detect from default locations
    for path in DEFAULT_DB_PATHS:
        if path.exists():
            return path

    raise FileNotFoundError(
        "CrossRef database not found. Set CROSSREF_LOCAL_DB environment variable "
        f"or place database at one of: {[str(p) for p in DEFAULT_DB_PATHS]}"
    )


class Config:
    """Configuration container."""

    _db_path: Optional[Path] = None

    @classmethod
    def get_db_path(cls) -> Path:
        """Get or auto-detect database path."""
        if cls._db_path is None:
            cls._db_path = get_db_path()
        return cls._db_path

    @classmethod
    def set_db_path(cls, path: str | Path) -> None:
        """Set database path explicitly."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Database not found: {path}")
        cls._db_path = path

    @classmethod
    def reset(cls) -> None:
        """Reset configuration (for testing)."""
        cls._db_path = None
