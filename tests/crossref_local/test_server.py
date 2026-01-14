"""Tests for crossref_local.server module (FastAPI HTTP server)."""

import json
import pytest

from fastapi.testclient import TestClient

from crossref_local.server import app


@pytest.fixture
def client():
    """Create FastAPI test client."""
    return TestClient(app)


class TestRootEndpoint:
    """Tests for / endpoint."""

    def test_root_returns_api_info(self, client):
        """GET / returns API information."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "endpoints" in data

    def test_root_lists_endpoints(self, client):
        """GET / lists available endpoints."""
        response = client.get("/")
        data = response.json()
        endpoints = data["endpoints"]
        assert "health" in endpoints
        assert "info" in endpoints


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_returns_healthy(self, client):
        """GET /health returns healthy status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database_connected" in data


class TestInfoEndpoint:
    """Tests for /info endpoint."""

    def test_info_returns_stats(self, client):
        """GET /info returns database statistics."""
        response = client.get("/info")
        assert response.status_code == 200
        data = response.json()
        assert "total_papers" in data
        assert "fts_indexed" in data
        assert isinstance(data["total_papers"], int)


class TestWorksSearchEndpoint:
    """Tests for /works endpoint (search)."""

    def test_search_requires_query(self, client):
        """GET /works requires q parameter."""
        response = client.get("/works")
        assert response.status_code == 422  # Validation error

    def test_search_returns_results(self, client):
        """GET /works?q=query returns search results."""
        response = client.get("/works?q=cancer&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "total" in data
        assert "results" in data
        assert data["query"] == "cancer"

    def test_search_respects_limit(self, client):
        """GET /works respects limit parameter."""
        response = client.get("/works?q=biology&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) <= 5

    def test_search_includes_elapsed_time(self, client):
        """GET /works includes elapsed_ms."""
        response = client.get("/works?q=physics&limit=1")
        data = response.json()
        assert "elapsed_ms" in data
        assert isinstance(data["elapsed_ms"], (int, float))

    def test_search_results_have_doi(self, client):
        """Search results include DOI."""
        response = client.get("/works?q=medicine&limit=3")
        data = response.json()
        for work in data["results"]:
            assert "doi" in work
            assert work["doi"].startswith("10.")


class TestWorksGetEndpoint:
    """Tests for /works/{doi} endpoint."""

    def test_get_nonexistent_doi_returns_404(self, client):
        """GET /works/{doi} returns 404 for nonexistent DOI."""
        response = client.get("/works/10.9999/nonexistent")
        assert response.status_code == 404

    def test_get_valid_doi_returns_work(self, client):
        """GET /works/{doi} returns work for valid DOI."""
        # First search to find a valid DOI
        search = client.get("/works?q=test&limit=1")
        if search.status_code == 200 and search.json()["results"]:
            doi = search.json()["results"][0]["doi"]
            response = client.get(f"/works/{doi}")
            assert response.status_code == 200
            data = response.json()
            assert data["doi"] == doi


class TestWorksBatchEndpoint:
    """Tests for /works/batch endpoint."""

    def test_batch_returns_results(self, client):
        """POST /works/batch returns batch results."""
        # First get some valid DOIs
        search = client.get("/works?q=science&limit=3")
        if search.status_code == 200 and search.json()["results"]:
            dois = [w["doi"] for w in search.json()["results"]]
            response = client.post("/works/batch", json={"dois": dois})
            assert response.status_code == 200
            data = response.json()
            assert "requested" in data
            assert "found" in data
            assert "results" in data

    def test_batch_with_empty_list(self, client):
        """POST /works/batch handles empty list."""
        response = client.post("/works/batch", json={"dois": []})
        assert response.status_code == 200
        data = response.json()
        assert data["requested"] == 0
        assert data["found"] == 0


class TestBackwardsCompatibleEndpoints:
    """Tests for backwards-compatible /api/* endpoints."""

    def test_api_search_endpoint(self, client):
        """GET /api/search/ works for backwards compatibility."""
        response = client.get("/api/search/?q=cancer&limit=3")
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    def test_api_stats_endpoint(self, client):
        """GET /api/stats/ works for backwards compatibility."""
        response = client.get("/api/stats/")
        assert response.status_code == 200
        data = response.json()
        assert "total_papers" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
