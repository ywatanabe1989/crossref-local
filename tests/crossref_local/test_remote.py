"""Tests for crossref_local.remote module.

No mocks: an in-process ``http.server.HTTPServer`` is spun up on a
free port and ``RemoteClient`` makes real HTTP calls against it. The
handler factory exposes a per-route response table whose entries can
be a JSON-serialisable dict (200 OK), an HTTP status integer, or
``"refuse"`` to close the connection (simulating connection refused).
"""

from __future__ import annotations

import json
import socket
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

import pytest

from crossref_local._core.models import SearchResult, Work
from crossref_local.remote import RemoteClient, get_client, reset_client


@dataclass
class RouteTable:
    """Mutable per-test route table consumed by the request handler."""

    routes: dict[tuple[str, str], Any] = field(default_factory=dict)
    body_log: list[bytes] = field(default_factory=list)

    def set(self, method: str, path: str, response: Any) -> None:
        self.routes[(method.upper(), path)] = response


def _make_handler(table: RouteTable) -> type[BaseHTTPRequestHandler]:
    class _Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            # silence test output
            return

        def _route_key(self) -> tuple[str, str]:
            path = self.path.split("?", 1)[0]
            return (self.command, path)

        def _respond(self, payload: Any) -> None:
            if isinstance(payload, int):
                self.send_response(payload)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b"{}")
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            body = json.dumps(payload).encode("utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            key = self._route_key()
            payload = table.routes.get(key, 404)
            self._respond(payload)

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0") or "0")
            if length:
                table.body_log.append(self.rfile.read(length))
            key = self._route_key()
            payload = table.routes.get(key, 404)
            self._respond(payload)

    return _Handler


@pytest.fixture
def api_server():
    """Spin up a real HTTP server on a free port; yield (base_url, table)."""

    table = RouteTable()
    server = HTTPServer(("127.0.0.1", 0), _make_handler(table))
    base_url = f"http://127.0.0.1:{server.server_port}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield base_url, table
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


# ---------- RemoteClient initialisation ----------


def test_remote_client_stores_normalised_base_url():
    # Arrange
    url = "http://localhost:8333"
    # Act
    client = RemoteClient(url)
    # Assert
    assert client.base_url == url


def test_remote_client_strips_trailing_slash_from_base_url():
    # Arrange
    url = "http://localhost:8333/"
    # Act
    client = RemoteClient(url)
    # Assert
    assert client.base_url == "http://localhost:8333"


def test_remote_client_records_custom_timeout_argument():
    # Arrange
    timeout = 60
    # Act
    client = RemoteClient("http://localhost:8333", timeout=timeout)
    # Assert
    assert client.timeout == timeout


def test_remote_client_uses_default_30s_timeout_when_unset():
    # Arrange
    # Act
    client = RemoteClient("http://localhost:8333")
    # Assert
    assert client.timeout == 30


# ---------- health ----------


def test_remote_client_health_returns_status_payload(api_server):
    # Arrange
    base_url, table = api_server
    table.set("GET", "/health", {"status": "healthy", "database_connected": True})
    client = RemoteClient(base_url)
    # Act
    result = client.health()
    # Assert
    assert result["status"] == "healthy"


# ---------- info ----------


def test_remote_client_info_reports_remote_mode(api_server):
    # Arrange
    base_url, table = api_server
    table.set("GET", "/", {"version": "1.0.0", "status": "running"})
    table.set(
        "GET",
        "/info",
        {"total_papers": 1000, "fts_indexed": 1000, "citations": 500},
    )
    client = RemoteClient(base_url)
    # Act
    result = client.info()
    # Assert
    assert result["mode"] == "remote"


def test_remote_client_info_includes_api_url_in_result(api_server):
    # Arrange
    base_url, table = api_server
    table.set("GET", "/", {"version": "1.0.0", "status": "running"})
    table.set("GET", "/info", {"total_papers": 1})
    client = RemoteClient(base_url)
    # Act
    result = client.info()
    # Assert
    assert result["api_url"] == base_url


# ---------- search ----------


def test_remote_client_search_returns_search_result_instance(api_server):
    # Arrange
    base_url, table = api_server
    table.set(
        "GET",
        "/works",
        {
            "query": "machine learning",
            "total": 100,
            "returned": 2,
            "elapsed_ms": 15.5,
            "results": [
                {"doi": "10.1234/test1", "title": "Paper 1", "authors": [], "year": 2023},
                {"doi": "10.1234/test2", "title": "Paper 2", "authors": [], "year": 2022},
            ],
        },
    )
    client = RemoteClient(base_url)
    # Act
    result = client.search(query="machine learning", limit=10)
    # Assert
    assert isinstance(result, SearchResult)


def test_remote_client_search_propagates_total_from_server(api_server):
    # Arrange
    base_url, table = api_server
    table.set(
        "GET",
        "/works",
        {
            "query": "machine learning",
            "total": 100,
            "returned": 2,
            "elapsed_ms": 15.5,
            "results": [
                {"doi": "10.1234/test1", "title": "Paper 1", "authors": [], "year": 2023},
            ],
        },
    )
    client = RemoteClient(base_url)
    # Act
    result = client.search(query="machine learning", limit=10)
    # Assert
    assert result.total == 100


def test_remote_client_search_parses_results_into_work_objects(api_server):
    # Arrange
    base_url, table = api_server
    table.set(
        "GET",
        "/works",
        {
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
            ],
        },
    )
    client = RemoteClient(base_url)
    # Act
    result = client.search(query="test")
    # Assert
    assert isinstance(result.works[0], Work)


def test_remote_client_search_preserves_doi_field_of_first_work(api_server):
    # Arrange
    base_url, table = api_server
    table.set(
        "GET",
        "/works",
        {
            "query": "test",
            "total": 1,
            "returned": 1,
            "elapsed_ms": 10.0,
            "results": [
                {"doi": "10.1234/test", "title": "Test Paper", "authors": [], "year": 2023}
            ],
        },
    )
    client = RemoteClient(base_url)
    # Act
    result = client.search(query="test")
    # Assert
    assert result.works[0].doi == "10.1234/test"


def test_remote_client_search_returns_empty_works_for_empty_results(api_server):
    # Arrange
    base_url, table = api_server
    table.set(
        "GET",
        "/works",
        {
            "query": "xyznonexistent",
            "total": 0,
            "returned": 0,
            "elapsed_ms": 5.0,
            "results": [],
        },
    )
    client = RemoteClient(base_url)
    # Act
    result = client.search(query="xyznonexistent")
    # Assert
    assert result.works == []


# ---------- get / exists ----------


def test_remote_client_get_returns_work_for_existing_doi(api_server):
    # Arrange
    base_url, table = api_server
    table.set(
        "GET",
        "/works/10.1234/test",
        {
            "doi": "10.1234/test",
            "title": "Test Paper",
            "authors": ["Author"],
            "year": 2023,
        },
    )
    client = RemoteClient(base_url)
    # Act
    work = client.get("10.1234/test")
    # Assert
    assert isinstance(work, Work)


def test_remote_client_get_returns_none_for_unknown_doi(api_server):
    # Arrange
    base_url, _ = api_server  # no route registered → 404
    client = RemoteClient(base_url)
    # Act
    work = client.get("10.0000/nonexistent")
    # Assert
    assert work is None


def test_remote_client_exists_returns_true_for_existing_doi(api_server):
    # Arrange
    base_url, table = api_server
    table.set(
        "GET",
        "/works/10.1234/test",
        {"doi": "10.1234/test", "title": "Test"},
    )
    client = RemoteClient(base_url)
    # Act
    found = client.exists("10.1234/test")
    # Assert
    assert found is True


def test_remote_client_exists_returns_false_for_unknown_doi(api_server):
    # Arrange
    base_url, _ = api_server  # no route registered → 404
    client = RemoteClient(base_url)
    # Act
    found = client.exists("10.0000/nonexistent")
    # Assert
    assert found is False


# ---------- get_many (batch endpoint) ----------


def test_remote_client_get_many_returns_list_of_works(api_server):
    # Arrange
    base_url, table = api_server
    table.set(
        "POST",
        "/works/batch",
        {
            "requested": 2,
            "found": 2,
            "results": [
                {"doi": "10.1234/test1", "title": "Paper 1", "authors": []},
                {"doi": "10.1234/test2", "title": "Paper 2", "authors": []},
            ],
        },
    )
    client = RemoteClient(base_url)
    # Act
    works = client.get_many(["10.1234/test1", "10.1234/test2"])
    # Assert
    assert all(isinstance(w, Work) for w in works)


def test_remote_client_get_many_returns_count_matching_server_results(api_server):
    # Arrange
    base_url, table = api_server
    table.set(
        "POST",
        "/works/batch",
        {
            "requested": 2,
            "found": 2,
            "results": [
                {"doi": "10.1234/test1", "title": "Paper 1", "authors": []},
                {"doi": "10.1234/test2", "title": "Paper 2", "authors": []},
            ],
        },
    )
    client = RemoteClient(base_url)
    # Act
    works = client.get_many(["10.1234/test1", "10.1234/test2"])
    # Assert
    assert len(works) == 2


def test_remote_client_get_many_returns_empty_list_for_empty_input(api_server):
    # Arrange
    base_url, table = api_server
    table.set("POST", "/works/batch", {"requested": 0, "found": 0, "results": []})
    client = RemoteClient(base_url)
    # Act
    works = client.get_many([])
    # Assert
    assert works == []


# ---------- connection / HTTP error mapping ----------


def test_remote_client_health_raises_connection_error_for_unreachable_server():
    # Arrange
    # Use a free port nobody is listening on → connection refused.
    port = _find_free_port()
    client = RemoteClient(f"http://127.0.0.1:{port}", timeout=1)
    # Act
    ctx = pytest.raises(ConnectionError)
    # Assert
    with ctx:
        client.health(timeout=1)


def test_remote_client_health_raises_connection_error_for_http_500(api_server):
    # Arrange
    base_url, table = api_server
    table.set("GET", "/health", 500)
    client = RemoteClient(base_url)
    # Act
    ctx = pytest.raises(ConnectionError)
    # Assert
    with ctx:
        client.health()


# ---------- singleton helpers ----------


def test_get_client_returns_remote_client_instance():
    # Arrange
    reset_client()
    # Act
    client = get_client("http://localhost:8333")
    # Assert
    assert isinstance(client, RemoteClient)


def test_get_client_returns_same_instance_for_same_url():
    # Arrange
    reset_client()
    first = get_client("http://localhost:8333")
    # Act
    second = get_client("http://localhost:8333")
    # Assert
    assert first is second


def test_get_client_returns_new_instance_for_different_url():
    # Arrange
    reset_client()
    first = get_client("http://localhost:8333")
    # Act
    second = get_client("http://localhost:8080")
    # Assert
    assert first is not second


def test_reset_client_drops_cached_singleton_so_next_call_is_fresh():
    # Arrange
    reset_client()
    first = get_client("http://localhost:8333")
    # Act
    reset_client()
    second = get_client("http://localhost:8333")
    # Assert
    assert first is not second
