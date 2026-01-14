"""Tests for crossref_local.remote module."""

import json
import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from crossref_local.remote import RemoteClient, get_client, reset_client
from crossref_local.models import Work, SearchResult


class MockResponse:
    """Mock urllib response."""

    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def read(self):
        return json.dumps(self.data).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class TestRemoteClientInit:
    """Tests for RemoteClient initialization."""

    def test_client_creation(self):
        """RemoteClient can be created."""
        client = RemoteClient("http://localhost:8333")
        assert client.base_url == "http://localhost:8333"

    def test_client_strips_trailing_slash(self):
        """RemoteClient strips trailing slash from URL."""
        client = RemoteClient("http://localhost:8333/")
        assert client.base_url == "http://localhost:8333"

    def test_client_custom_timeout(self):
        """RemoteClient accepts custom timeout."""
        client = RemoteClient("http://localhost:8333", timeout=60)
        assert client.timeout == 60

    def test_client_default_timeout(self):
        """RemoteClient has default timeout."""
        client = RemoteClient("http://localhost:8333")
        assert client.timeout == 30


class TestRemoteClientHealth:
    """Tests for RemoteClient.health method."""

    @patch("urllib.request.urlopen")
    def test_health_returns_dict(self, mock_urlopen):
        """health() returns dictionary."""
        mock_urlopen.return_value = MockResponse({
            "status": "healthy",
            "database_connected": True,
        })
        client = RemoteClient("http://localhost:8333")
        result = client.health()
        assert isinstance(result, dict)
        assert result["status"] == "healthy"


class TestRemoteClientInfo:
    """Tests for RemoteClient.info method."""

    @patch("urllib.request.urlopen")
    def test_info_returns_dict(self, mock_urlopen):
        """info() returns dictionary with API info."""
        # Mock needs to handle two requests: root and /info
        responses = [
            MockResponse({"version": "1.0.0", "status": "running"}),
            MockResponse({"total_papers": 1000, "fts_indexed": 1000, "citations": 500}),
        ]
        mock_urlopen.side_effect = responses

        client = RemoteClient("http://localhost:8333")
        result = client.info()

        assert isinstance(result, dict)
        assert "api_url" in result
        assert result["mode"] == "remote"


class TestRemoteClientSearch:
    """Tests for RemoteClient.search method."""

    @patch("urllib.request.urlopen")
    def test_search_returns_search_result(self, mock_urlopen):
        """search() returns SearchResult."""
        mock_urlopen.return_value = MockResponse({
            "query": "machine learning",
            "total": 100,
            "returned": 2,
            "elapsed_ms": 15.5,
            "results": [
                {"doi": "10.1234/test1", "title": "Paper 1", "authors": [], "year": 2023},
                {"doi": "10.1234/test2", "title": "Paper 2", "authors": [], "year": 2022},
            ]
        })

        client = RemoteClient("http://localhost:8333")
        result = client.search(query="machine learning", limit=10)

        assert isinstance(result, SearchResult)
        assert result.total == 100
        assert len(result.works) == 2

    @patch("urllib.request.urlopen")
    def test_search_returns_work_objects(self, mock_urlopen):
        """search() returns Work objects in results."""
        mock_urlopen.return_value = MockResponse({
            "query": "test",
            "total": 1,
            "returned": 1,
            "elapsed_ms": 10.0,
            "results": [
                {
                    "doi": "10.1234/test",
                    "title": "Test Paper",
                    "authors": ["Author One"],
                    "year": 2023,
                    "journal": "Test Journal",
                }
            ]
        })

        client = RemoteClient("http://localhost:8333")
        result = client.search(query="test")

        assert len(result.works) == 1
        assert isinstance(result.works[0], Work)
        assert result.works[0].doi == "10.1234/test"
        assert result.works[0].title == "Test Paper"

    @patch("urllib.request.urlopen")
    def test_search_empty_results(self, mock_urlopen):
        """search() handles empty results."""
        mock_urlopen.return_value = MockResponse({
            "query": "xyznonexistent",
            "total": 0,
            "returned": 0,
            "elapsed_ms": 5.0,
            "results": []
        })

        client = RemoteClient("http://localhost:8333")
        result = client.search(query="xyznonexistent")

        assert result.total == 0
        assert result.works == []


class TestRemoteClientGet:
    """Tests for RemoteClient.get method."""

    @patch("urllib.request.urlopen")
    def test_get_returns_work(self, mock_urlopen):
        """get() returns Work for existing DOI."""
        mock_urlopen.return_value = MockResponse({
            "doi": "10.1234/test",
            "title": "Test Paper",
            "authors": ["Author"],
            "year": 2023,
        })

        client = RemoteClient("http://localhost:8333")
        work = client.get("10.1234/test")

        assert isinstance(work, Work)
        assert work.doi == "10.1234/test"

    @patch("urllib.request.urlopen")
    def test_get_returns_none_for_missing(self, mock_urlopen):
        """get() returns None for nonexistent DOI."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://localhost:8333/works/10.0000/nonexistent",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )

        client = RemoteClient("http://localhost:8333")
        work = client.get("10.0000/nonexistent")

        assert work is None


class TestRemoteClientGetMany:
    """Tests for RemoteClient.get_many method."""

    @patch("urllib.request.urlopen")
    def test_get_many_returns_list(self, mock_urlopen):
        """get_many() returns list of Works."""
        mock_urlopen.return_value = MockResponse({
            "requested": 2,
            "found": 2,
            "results": [
                {"doi": "10.1234/test1", "title": "Paper 1", "authors": []},
                {"doi": "10.1234/test2", "title": "Paper 2", "authors": []},
            ]
        })

        client = RemoteClient("http://localhost:8333")
        works = client.get_many(["10.1234/test1", "10.1234/test2"])

        assert isinstance(works, list)
        assert len(works) == 2
        for work in works:
            assert isinstance(work, Work)

    @patch("urllib.request.urlopen")
    def test_get_many_empty_list(self, mock_urlopen):
        """get_many() with empty list returns empty list."""
        mock_urlopen.return_value = MockResponse({
            "requested": 0,
            "found": 0,
            "results": []
        })

        client = RemoteClient("http://localhost:8333")
        works = client.get_many([])

        assert works == []


class TestRemoteClientExists:
    """Tests for RemoteClient.exists method."""

    @patch("urllib.request.urlopen")
    def test_exists_returns_true(self, mock_urlopen):
        """exists() returns True for existing DOI."""
        mock_urlopen.return_value = MockResponse({
            "doi": "10.1234/test",
            "title": "Test",
        })

        client = RemoteClient("http://localhost:8333")
        assert client.exists("10.1234/test") is True

    @patch("urllib.request.urlopen")
    def test_exists_returns_false(self, mock_urlopen):
        """exists() returns False for nonexistent DOI."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://localhost:8333/works/10.0000/nonexistent",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )

        client = RemoteClient("http://localhost:8333")
        assert client.exists("10.0000/nonexistent") is False


class TestRemoteClientConnectionErrors:
    """Tests for RemoteClient connection error handling."""

    @patch("urllib.request.urlopen")
    def test_connection_error_raises(self, mock_urlopen):
        """Connection errors raise ConnectionError."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

        client = RemoteClient("http://localhost:8333")
        with pytest.raises(ConnectionError):
            client.health()

    @patch("urllib.request.urlopen")
    def test_http_error_raises(self, mock_urlopen):
        """HTTP errors (non-404) raise ConnectionError."""
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="http://localhost:8333/health",
            code=500,
            msg="Internal Server Error",
            hdrs={},
            fp=None,
        )

        client = RemoteClient("http://localhost:8333")
        with pytest.raises(ConnectionError):
            client.health()


class TestSingletonClient:
    """Tests for module-level singleton client."""

    def test_get_client_returns_client(self):
        """get_client() returns RemoteClient."""
        reset_client()
        client = get_client("http://localhost:8333")
        assert isinstance(client, RemoteClient)

    def test_get_client_singleton(self):
        """get_client() returns same instance."""
        reset_client()
        client1 = get_client("http://localhost:8333")
        client2 = get_client("http://localhost:8333")
        assert client1 is client2

    def test_get_client_new_url(self):
        """get_client() creates new instance for different URL."""
        reset_client()
        client1 = get_client("http://localhost:8333")
        client2 = get_client("http://localhost:8080")
        assert client1 is not client2

    def test_reset_client(self):
        """reset_client() clears singleton."""
        reset_client()
        client1 = get_client("http://localhost:8333")
        reset_client()
        client2 = get_client("http://localhost:8333")
        assert client1 is not client2
