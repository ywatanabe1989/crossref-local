"""Tests for crossref_local.config module.

No mocks: env vars are managed by a yield-based save/restore fixture
and DB paths are real files under ``tmp_path``.
"""

import os
from pathlib import Path

import pytest

from crossref_local._core.config import (
    DEFAULT_API_URLS,
    DEFAULT_DB_PATHS,
    Config,
    get_db_path,
)


@pytest.fixture
def crossref_local_db_env():
    """Yield-based env save/restore for CROSSREF_LOCAL_DB."""
    # Arrange
    saved = os.environ.get("CROSSREF_LOCAL_DB")

    def setter(value: str) -> None:
        os.environ["CROSSREF_LOCAL_DB"] = value
        Config.reset()

    try:
        yield setter
    finally:
        if saved is None:
            os.environ.pop("CROSSREF_LOCAL_DB", None)
        else:
            os.environ["CROSSREF_LOCAL_DB"] = saved
        Config.reset()


# ---------- get_db_path ----------


def test_get_db_path_returns_path_from_env_variable(tmp_path, crossref_local_db_env):
    # Arrange
    db_file = tmp_path / "test.db"
    db_file.touch()
    crossref_local_db_env(str(db_file))
    # Act
    result = get_db_path()
    # Assert
    assert result == db_file


def test_get_db_path_raises_filenotfound_for_nonexistent_env_path(
    crossref_local_db_env,
):
    # Arrange
    crossref_local_db_env("/nonexistent/path.db")
    # Act
    ctx = pytest.raises(FileNotFoundError)
    # Assert
    with ctx:
        get_db_path()


def test_get_db_path_includes_offending_path_in_error_message(crossref_local_db_env):
    # Arrange
    crossref_local_db_env("/nonexistent/path.db")
    # Act
    try:
        get_db_path()
        raise AssertionError("expected FileNotFoundError")
    except FileNotFoundError as exc:
        msg = str(exc)
    # Assert
    assert "/nonexistent/path.db" in msg


def test_get_db_path_autodetects_existing_default_database():
    # Arrange
    Config.reset()
    # Act
    try:
        path = get_db_path()
    except FileNotFoundError:
        pytest.skip("No database available for auto-detection test")
    # Assert
    assert path.exists()


# ---------- Config ----------


def test_config_get_db_path_caches_result_across_calls():
    # Arrange
    Config.reset()
    try:
        first = Config.get_db_path()
    except FileNotFoundError:
        pytest.skip("No database available")
    # Act
    second = Config.get_db_path()
    # Assert
    assert first == second


def test_config_set_db_path_accepts_existing_file(tmp_path):
    # Arrange
    Config.reset()
    db_file = tmp_path / "custom.db"
    db_file.touch()
    # Act
    Config.set_db_path(db_file)
    # Assert
    assert Config.get_db_path() == db_file


def test_config_set_db_path_raises_filenotfound_for_invalid_path():
    # Arrange
    Config.reset()
    # Act
    ctx = pytest.raises(FileNotFoundError)
    # Assert
    with ctx:
        Config.set_db_path("/nonexistent/database.db")


def test_config_reset_clears_cached_db_path(tmp_path):
    # Arrange
    Config.reset()
    db_file = tmp_path / "test.db"
    db_file.touch()
    Config.set_db_path(db_file)
    # Act
    Config.reset()
    # Assert
    assert Config._db_path is None


def test_config_set_mode_switches_to_http_mode():
    # Arrange
    Config.reset()
    # Act
    Config.set_mode("http")
    # Assert
    assert Config.get_mode() == "http"


def test_config_set_api_url_stores_supplied_url():
    # Arrange
    Config.reset()
    # Act
    Config.set_api_url("http://example.com:8333")
    # Assert
    assert Config.get_api_url() == "http://example.com:8333"


def test_config_set_api_url_implicitly_enables_http_mode():
    # Arrange
    Config.reset()
    # Act
    Config.set_api_url("http://example.com:8333")
    # Assert
    assert Config.get_mode() == "http"


# ---------- defaults ----------


def test_default_db_paths_are_all_pathlib_path_instances():
    # Arrange
    paths = DEFAULT_DB_PATHS
    # Act
    non_paths = [p for p in paths if not isinstance(p, Path)]
    # Assert
    assert non_paths == []


def test_default_api_urls_are_all_http_or_https_strings():
    # Arrange
    urls = DEFAULT_API_URLS
    # Act
    bad = [u for u in urls if not (isinstance(u, str) and u.startswith("http"))]
    # Assert
    assert bad == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
