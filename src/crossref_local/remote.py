"""Remote API client for crossref_local.

Connects to a CrossRef Local API server instead of direct database access.
Use this when the database is on a remote server accessible via HTTP.
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Optional, Dict, Any

from .models import Work, SearchResult


class RemoteClient:
    """
    HTTP client for CrossRef Local API server.

    Provides the same interface as the local API but connects
    to a remote server via HTTP.

    Example:
        >>> client = RemoteClient("http://localhost:3333")
        >>> results = client.search(title="machine learning", limit=10)
        >>> work = client.get("10.1038/nature12373")
    """

    def __init__(self, base_url: str = "http://localhost:3333", timeout: int = 30):
        """
        Initialize remote client.

        Args:
            base_url: API server URL (default: http://localhost:3333)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        """Make HTTP GET request to API."""
        url = f"{self.base_url}{endpoint}"
        if params:
            # Filter out None values
            params = {k: v for k, v in params.items() if v is not None}
            if params:
                url = f"{url}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url)
            req.add_header("Accept", "application/json")
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise ConnectionError(f"API request failed: {e.code} {e.reason}") from e
        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Cannot connect to API at {self.base_url}: {e.reason}"
            ) from e

    def health(self) -> Dict:
        """Check API server health."""
        return self._request("/health")

    def info(self) -> Dict:
        """Get database/API information."""
        root = self._request("/")
        info_data = self._request("/info")
        return {
            "api_url": self.base_url,
            "api_version": root.get("version", "unknown"),
            "status": root.get("status", "unknown"),
            "mode": "remote",
            "works": info_data.get("total_papers", 0) if info_data else 0,
            "fts_indexed": info_data.get("fts_indexed", 0) if info_data else 0,
            "citations": info_data.get("citations", 0) if info_data else 0,
        }

    def search(
        self,
        query: Optional[str] = None,
        doi: Optional[str] = None,
        title: Optional[str] = None,
        authors: Optional[str] = None,
        year: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> SearchResult:
        """
        Search for papers.

        Args:
            query: Full-text search query (searches title by default)
            doi: Search by DOI
            title: Search by title (explicit)
            authors: Search by author name
            year: Filter by publication year
            limit: Maximum results (default: 10, max: 100)
            offset: Skip first N results for pagination

        Returns:
            SearchResult with matching works
        """
        # Use new /works endpoint with FTS5 search
        search_query = query or title

        params = {
            "q": search_query,
            "limit": min(limit, 100),
            "offset": offset,
        }

        data = self._request("/works", params)

        if not data:
            return SearchResult(works=[], total=0, query=query or "", elapsed_ms=0.0)

        works = []
        for item in data.get("results", []):
            work = Work(
                doi=item.get("doi", ""),
                title=item.get("title", ""),
                authors=item.get("authors", []),
                year=item.get("year"),
                journal=item.get("journal"),
                volume=item.get("volume"),
                issue=item.get("issue"),
                page=item.get("page") or item.get("pages"),
                abstract=item.get("abstract"),
                citation_count=item.get("citation_count"),
            )
            works.append(work)

        return SearchResult(
            works=works,
            total=data.get("total", len(works)),
            query=query or title or doi or "",
            elapsed_ms=data.get("elapsed_ms", 0.0),
        )

    def get(self, doi: str) -> Optional[Work]:
        """
        Get a work by DOI.

        Args:
            doi: Digital Object Identifier

        Returns:
            Work object or None if not found
        """
        # Use /works/{doi} endpoint directly
        data = self._request(f"/works/{doi}")
        if not data or "error" in data:
            return None

        return Work(
            doi=data.get("doi", doi),
            title=data.get("title", ""),
            authors=data.get("authors", []),
            year=data.get("year"),
            journal=data.get("journal"),
            volume=data.get("volume"),
            issue=data.get("issue"),
            page=data.get("page"),
            abstract=data.get("abstract"),
            citation_count=data.get("citation_count"),
        )

    def get_many(self, dois: List[str]) -> List[Work]:
        """
        Get multiple works by DOI using batch endpoint.

        Args:
            dois: List of DOIs

        Returns:
            List of Work objects
        """
        # Use batch endpoint if available
        try:
            data = {"dois": dois}
            req_data = json.dumps(data).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/works/batch", data=req_data, method="POST"
            )
            req.add_header("Content-Type", "application/json")
            req.add_header("Accept", "application/json")

            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))

            works = []
            for item in result.get("results", []):
                work = Work(
                    doi=item.get("doi", ""),
                    title=item.get("title", ""),
                    authors=item.get("authors", []),
                    year=item.get("year"),
                    journal=item.get("journal"),
                    volume=item.get("volume"),
                    issue=item.get("issue"),
                    page=item.get("page"),
                    abstract=item.get("abstract"),
                    citation_count=item.get("citation_count"),
                )
                works.append(work)
            return works
        except Exception:
            # Fallback to individual lookups
            works = []
            for doi in dois:
                work = self.get(doi)
                if work:
                    works.append(work)
            return works

    def exists(self, doi: str) -> bool:
        """Check if a DOI exists."""
        return self.get(doi) is not None

    def get_citations(self, doi: str, direction: str = "both") -> Dict:
        """
        Get citations for a paper.

        Args:
            doi: Paper DOI
            direction: 'citing', 'cited_by', or 'both'

        Returns:
            Dict with citation information
        """
        params = {"doi": doi, "direction": direction}
        return self._request("/api/citations/", params) or {}

    def get_journal(
        self, issn: Optional[str] = None, name: Optional[str] = None
    ) -> Dict:
        """
        Get journal information.

        Args:
            issn: Journal ISSN
            name: Journal name

        Returns:
            Dict with journal information
        """
        params = {"issn": issn, "name": name}
        return self._request("/api/journal/", params) or {}


# Module-level client for convenience
_client: Optional[RemoteClient] = None


def get_client(base_url: str = "http://localhost:3333") -> RemoteClient:
    """Get or create singleton remote client."""
    global _client
    if _client is None or _client.base_url != base_url:
        _client = RemoteClient(base_url)
    return _client


def reset_client() -> None:
    """Reset singleton client."""
    global _client
    _client = None
