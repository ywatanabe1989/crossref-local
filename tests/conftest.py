"""Pytest configuration and fixtures for crossref_local tests."""

import os
import pytest
from pathlib import Path

# Test database path
TEST_DB_PATH = Path(__file__).parent / "fixtures" / "test_crossref.db"


def _check_remote_api():
    """Check if remote API is available."""
    try:
        import urllib.request

        req = urllib.request.Request("http://localhost:3333/health", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def pytest_configure(config):
    """Configure pytest to use test database if available."""
    if TEST_DB_PATH.exists():
        os.environ["CROSSREF_LOCAL_DB"] = str(TEST_DB_PATH)
        print(f"\nUsing test database: {TEST_DB_PATH}")
    else:
        # Check if real database is available
        from crossref_local.config import DEFAULT_DB_PATHS

        for path in DEFAULT_DB_PATHS:
            if path.exists():
                print(f"\nUsing real database: {path}")
                break
        else:
            # Check if remote API is available (allows running mocked tests)
            if _check_remote_api():
                os.environ["CROSSREF_LOCAL_MODE"] = "remote"
                print("\nNo local database, using remote API mode")
            else:
                # Allow mocked tests to run without database
                print("\nNo database found - only mocked tests will work")


@pytest.fixture
def test_db_path():
    """Return path to test database."""
    return TEST_DB_PATH


@pytest.fixture
def sample_doi():
    """Return a known DOI from the test database."""
    # This will be available after running create_test_db.py
    return "10.1126/science.aax0758"
