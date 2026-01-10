"""Pytest configuration and fixtures for crossref_local tests."""

import os
import pytest
from pathlib import Path

# Test database path
TEST_DB_PATH = Path(__file__).parent / "fixtures" / "test_crossref.db"


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
            pytest.exit(
                "No database found!\n"
                "Run: python scripts/create_test_db.py\n"
                "Or: make test-db-create"
            )


@pytest.fixture
def test_db_path():
    """Return path to test database."""
    return TEST_DB_PATH


@pytest.fixture
def sample_doi():
    """Return a known DOI from the test database."""
    # This will be available after running create_test_db.py
    return "10.1126/science.aax0758"
