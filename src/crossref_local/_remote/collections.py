"""Collection methods mixin for RemoteClient."""

import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, List, Optional, Any


class CollectionsMixin:
    """Mixin providing collection management methods for RemoteClient."""

    def list_collections(self) -> List[Dict]:
        """
        List all collections.

        Returns:
            List of collection info dictionaries
        """
        data = self._request("/collections")
        if not data:
            return []
        return data.get("collections", [])

    def create_collection(
        self,
        name: str,
        query: Optional[str] = None,
        dois: Optional[List[str]] = None,
        limit: int = 1000,
    ) -> Dict:
        """
        Create a new collection from search query or DOI list.

        Args:
            name: Collection name
            query: FTS search query (if dois not provided)
            dois: Explicit list of DOIs
            limit: Max papers for query mode

        Returns:
            Collection info dictionary
        """
        body = {"name": name, "limit": limit}
        if query:
            body["query"] = query
        if dois:
            body["dois"] = dois

        result = self._request("/collections", method="POST", data=body)
        return result or {}

    def get_collection(
        self,
        name: str,
        fields: Optional[List[str]] = None,
        include_abstract: bool = False,
        include_references: bool = False,
        include_citations: bool = False,
        year_min: Optional[int] = None,
        year_max: Optional[int] = None,
        journal: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> Dict:
        """
        Query a collection with field filtering.

        Args:
            name: Collection name
            fields: Explicit field list
            include_abstract: Include abstracts
            include_references: Include references
            include_citations: Include citation counts
            year_min: Filter by min year
            year_max: Filter by max year
            journal: Filter by journal
            limit: Max results

        Returns:
            Dict with collection name, count, and papers
        """
        params = {
            "include_abstract": include_abstract,
            "include_references": include_references,
            "include_citations": include_citations,
            "year_min": year_min,
            "year_max": year_max,
            "journal": journal,
            "limit": limit,
        }
        if fields:
            params["fields"] = ",".join(fields)

        data = self._request(f"/collections/{name}", params)
        return data or {}

    def get_collection_stats(self, name: str) -> Dict:
        """
        Get collection statistics.

        Args:
            name: Collection name

        Returns:
            Dict with year distribution, top journals, citation stats
        """
        data = self._request(f"/collections/{name}/stats")
        return data or {}

    def download_collection(
        self,
        name: str,
        output_path: str,
        format: str = "json",
        fields: Optional[List[str]] = None,
    ) -> str:
        """
        Download collection as a file.

        Args:
            name: Collection name
            output_path: Local file path to save to
            format: Export format (json, csv, bibtex, dois)
            fields: Fields to include (json/csv)

        Returns:
            Output file path
        """
        params = {"format": format}
        if fields:
            params["fields"] = ",".join(fields)

        url = f"{self.base_url}/collections/{name}/download"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                content = response.read()
                with open(output_path, "wb") as f:
                    f.write(content)
            return output_path
        except urllib.error.HTTPError as e:
            raise ConnectionError(f"Download failed: {e.code} {e.reason}") from e
        except urllib.error.URLError as e:
            raise ConnectionError(f"Cannot connect: {e.reason}") from e

    def delete_collection(self, name: str) -> bool:
        """
        Delete a collection.

        Args:
            name: Collection name

        Returns:
            True if deleted
        """
        data = self._request(f"/collections/{name}", method="DELETE")
        if not data:
            return False
        return data.get("deleted", False)

    def collection_exists(self, name: str) -> bool:
        """
        Check if a collection exists.

        Args:
            name: Collection name

        Returns:
            True if exists
        """
        data = self._request(f"/collections/{name}/stats")
        return data is not None
