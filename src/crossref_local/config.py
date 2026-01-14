"""Configuration for crossref_local."""

import os
from pathlib import Path
from typing import Optional

# Default database locations (checked in order)
DEFAULT_DB_PATHS = [
    Path.cwd() / "data" / "crossref.db",
    Path.home() / ".crossref_local" / "crossref.db",
]

# Default remote API URL (via SSH tunnel)
DEFAULT_API_URLS = [
    "http://localhost:8333",  # SSH tunnel to NAS
]
DEFAULT_API_URL = DEFAULT_API_URLS[0]


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
    _api_url: Optional[str] = None
    _mode: str = "auto"  # "auto", "db", or "http"

    @classmethod
    def get_mode(cls) -> str:
        """
        Get current mode.

        Returns:
            "db" if using direct database access
            "http" if using HTTP API
        """
        if cls._mode == "auto":
            # Check environment variable
            env_mode = os.environ.get("CROSSREF_LOCAL_MODE", "").lower()
            if env_mode in ("http", "remote", "api"):
                return "http"
            if env_mode in ("db", "local"):
                return "db"

            # Check if API URL is set
            if cls._api_url or os.environ.get("CROSSREF_LOCAL_API_URL"):
                return "http"

            # Check if local database exists
            try:
                get_db_path()
                return "db"
            except FileNotFoundError:
                # No local DB, try http
                return "http"

        return cls._mode

    @classmethod
    def set_mode(cls, mode: str) -> None:
        """Set mode explicitly: 'db', 'http', or 'auto'."""
        if mode not in ("auto", "db", "http"):
            raise ValueError(f"Invalid mode: {mode}. Use 'auto', 'db', or 'http'")
        cls._mode = mode

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
        cls._mode = "db"

    @classmethod
    def get_api_url(cls, auto_detect: bool = True) -> str:
        """
        Get API URL for remote mode.

        Args:
            auto_detect: If True, test each URL and use first working one

        Returns:
            API URL string
        """
        if cls._api_url:
            return cls._api_url

        env_url = os.environ.get("CROSSREF_LOCAL_API_URL")
        if env_url:
            return env_url

        if auto_detect:
            working_url = cls._find_working_api()
            if working_url:
                cls._api_url = working_url
                return working_url

        return DEFAULT_API_URL

    @classmethod
    def _find_working_api(cls) -> Optional[str]:
        """Try each default API URL and return first working one."""
        import urllib.request
        import urllib.error

        for url in DEFAULT_API_URLS:
            try:
                req = urllib.request.Request(f"{url}/health", method="GET")
                req.add_header("Accept", "application/json")
                with urllib.request.urlopen(req, timeout=3) as response:
                    if response.status == 200:
                        return url
            except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
                continue
        return None

    @classmethod
    def set_api_url(cls, url: str) -> None:
        """Set API URL for http mode."""
        cls._api_url = url.rstrip("/")
        cls._mode = "http"

    @classmethod
    def reset(cls) -> None:
        """Reset configuration (for testing)."""
        cls._db_path = None
        cls._api_url = None
        cls._mode = "auto"
