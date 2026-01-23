"""Cache utility functions for crossref-local.

Provides path handling and validation utilities for the cache module.
"""

import os
import re
from pathlib import Path
from typing import Optional


# Valid cache name pattern: alphanumeric, underscores, hyphens only
_CACHE_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")


def sanitize_name(name: str) -> str:
    """Sanitize cache name to prevent path traversal.

    Args:
        name: Cache name to sanitize

    Returns:
        Sanitized name

    Raises:
        ValueError: If name contains invalid characters
    """
    if not name:
        raise ValueError("Cache name cannot be empty")
    if not _CACHE_NAME_PATTERN.match(name):
        raise ValueError(
            f"Invalid cache name '{name}': only alphanumeric, underscores, and hyphens allowed"
        )
    if len(name) > 64:
        raise ValueError(f"Cache name too long: {len(name)} chars (max 64)")
    return name


def get_cache_dir(user_id: Optional[str] = None) -> Path:
    """Get cache directory, creating if needed.

    Args:
        user_id: Optional user ID for multi-tenant scoping.
                 If provided, creates a user-specific subdirectory.
    """
    cache_dir = Path(
        os.environ.get(
            "CROSSREF_LOCAL_CACHE_DIR", Path.home() / ".cache" / "crossref-local"
        )
    )
    # Add user subdirectory for multi-tenant support
    if user_id:
        # Sanitize user_id as well
        safe_user_id = re.sub(r"[^a-zA-Z0-9_-]", "", user_id[:16])
        if safe_user_id:
            cache_dir = cache_dir / safe_user_id
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def cache_path(name: str, user_id: Optional[str] = None) -> Path:
    """Get path for a named cache.

    Args:
        name: Cache name (will be sanitized)
        user_id: Optional user ID for multi-tenant scoping

    Returns:
        Path to cache file
    """
    safe_name = sanitize_name(name)
    return get_cache_dir(user_id) / f"{safe_name}.json"


def meta_path(name: str, user_id: Optional[str] = None) -> Path:
    """Get path for cache metadata.

    Args:
        name: Cache name (will be sanitized)
        user_id: Optional user ID for multi-tenant scoping

    Returns:
        Path to metadata file
    """
    safe_name = sanitize_name(name)
    return get_cache_dir(user_id) / f"{safe_name}.meta.json"
