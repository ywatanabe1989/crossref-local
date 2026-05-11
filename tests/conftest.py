"""Pytest configuration and fixtures for crossref_local tests."""

import os
import pytest
from pathlib import Path

# Test database path
TEST_DB_PATH = Path(__file__).parent / "fixtures" / "test_crossref.db"

# Module-name allowlist of tests that DON'T need the local CrossRef DB
# (everything else gets auto-skipped when the DB is missing).
_DB_OPTIONAL_TEST_MODULES = frozenset(
    {
        "test_cli_completion",
        "test_config",
        "test_mcp_server",
        "test_cross_package_imports",
        "test_audit",
    }
)

# Set in `pytest_configure`; consumed by `pytest_collection_modifyitems`.
_DB_AVAILABLE = False


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
    """Configure pytest backing store: local DB > remote API > skip.

    Resolution order:

    1. Fixture DB at `tests/fixtures/test_crossref.db` (CI / local smoke).
    2. Any path in `DEFAULT_DB_PATHS` (includes
       `~/proj/crossref-local/data/crossref.db` — the canonical
       db-host-side install location).
    3. Remote relay/API reachable at the configured URL (when the
       package is in `http` mode pointing at a separate db-host via
       SSH tunnel; respects `CROSSREF_LOCAL_MODE=http`).
    4. Nothing available → DB-dependent tests skip, mocked subset still runs.
    """
    global _DB_AVAILABLE

    if TEST_DB_PATH.exists():
        os.environ["CROSSREF_LOCAL_DB"] = str(TEST_DB_PATH)
        _DB_AVAILABLE = True
        print(f"\nUsing test database: {TEST_DB_PATH}")
        return

    from crossref_local._core.config import DEFAULT_DB_PATHS

    for path in DEFAULT_DB_PATHS:
        if path.exists():
            _DB_AVAILABLE = True
            print(f"\nUsing real database: {path}")
            return

    # No local DB. Respect MODE=http: if a remote db-host is reachable
    # via a forwarded relay port (e.g. SSH `LocalForward 31291`), tests
    # can drive the package through its HTTP path instead of skipping.
    mode = os.environ.get("CROSSREF_LOCAL_MODE", "").lower()
    if mode == "http" and _check_remote_api():
        _DB_AVAILABLE = True
        print("\nNo local database; using remote relay via SSH tunnel (MODE=http)")
        return

    # Last-resort heuristic: remote API at default URL responds.
    if _check_remote_api():
        os.environ["CROSSREF_LOCAL_MODE"] = "http"
        _DB_AVAILABLE = True
        print("\nNo local database; default API URL responds — running via HTTP")
        return

    print("\nNo database found — DB-dependent tests will be skipped")


def pytest_collection_modifyitems(config, items):
    """Auto-skip DB-dependent tests when no DB is available.

    Without this hook, the conftest just prints a warning and the
    ~130 DB-touching tests fail with FileNotFoundError at runtime.
    With this hook, those tests SKIP cleanly so dev/CI environments
    without the 1.5 TB local CrossRef DB get a green run on the
    mocked subset only.
    """
    if _DB_AVAILABLE:
        return
    skip_no_db = pytest.mark.skip(
        reason="local CrossRef DB not present (only mocked tests run)"
    )
    for item in items:
        # `item.module.__name__` is e.g. "tests.crossref_local.test_aio"
        mod_short = item.module.__name__.rsplit(".", 1)[-1]
        if mod_short not in _DB_OPTIONAL_TEST_MODULES:
            item.add_marker(skip_no_db)


@pytest.fixture
def test_db_path():
    """Return path to test database."""
    return TEST_DB_PATH


@pytest.fixture
def sample_doi():
    """Return a known DOI from the test database."""
    # This will be available after running create_test_db.py
    return "10.1126/science.aax0758"
