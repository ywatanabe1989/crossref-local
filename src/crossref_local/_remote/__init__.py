"""Remote API client package with collection support.

Provides RemoteClient for connecting to CrossRef Local API server.
"""

from typing import Optional

from .base import (
    RemoteClient as _BaseClient,
    DEFAULT_API_URL,
)
from .collections import CollectionsMixin


class RemoteClient(CollectionsMixin, _BaseClient):
    """Remote client with collection support.

    Extends base RemoteClient with collection management methods.

    Example:
        >>> client = RemoteClient("http://localhost:31291")
        >>> # Create a collection
        >>> client.create_collection("epilepsy", query="epilepsy seizure")
        >>> # Query collection
        >>> papers = client.get_collection("epilepsy", fields=["doi", "title"])
        >>> # Download as file
        >>> client.download_collection("epilepsy", "papers.bib", format="bibtex")
    """

    pass


# Module-level client singleton
_client: Optional[RemoteClient] = None


def get_client(base_url: str = DEFAULT_API_URL) -> RemoteClient:
    """Get or create singleton remote client with collection support."""
    global _client
    if _client is None or _client.base_url != base_url:
        _client = RemoteClient(base_url)
    return _client


def reset_client() -> None:
    """Reset singleton client."""
    global _client
    _client = None


__all__ = [
    "RemoteClient",
    "DEFAULT_API_URL",
    "get_client",
    "reset_client",
]
