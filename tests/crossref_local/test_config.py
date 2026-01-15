"""Tests for crossref_local.config module."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch

from crossref_local.config import Config, get_db_path, DEFAULT_DB_PATHS, DEFAULT_API_URLS


class TestGetDbPath:
    """Tests for get_db_path function."""

    def test_returns_path_from_env_variable(self, tmp_path):
        """get_db_path() uses CROSSREF_LOCAL_DB env variable when set."""
        # Create a temporary database file
        db_file = tmp_path / "test.db"
        db_file.touch()

        with patch.dict(os.environ, {"CROSSREF_LOCAL_DB": str(db_file)}):
            Config.reset()
            result = get_db_path()
            assert result == db_file

    def test_raises_when_env_path_not_found(self):
        """get_db_path() raises FileNotFoundError for invalid env path."""
        with patch.dict(os.environ, {"CROSSREF_LOCAL_DB": "/nonexistent/path.db"}):
            Config.reset()
            with pytest.raises(FileNotFoundError) as exc_info:
                get_db_path()
            assert "CROSSREF_LOCAL_DB" in str(exc_info.value)

    def test_autodetects_from_default_paths(self):
        """get_db_path() finds database from default paths."""
        # This test relies on the actual database being available
        # Skip if no database exists
        Config.reset()
        try:
            path = get_db_path()
            assert path.exists()
            assert path.suffix == ".db"
        except FileNotFoundError:
            pytest.skip("No database available for auto-detection test")


class TestConfig:
    """Tests for Config class."""

    def setup_method(self):
        """Reset Config before each test."""
        Config.reset()

    def test_get_db_path_caches_result(self):
        """Config.get_db_path() caches the path."""
        try:
            path1 = Config.get_db_path()
            path2 = Config.get_db_path()
            assert path1 == path2
        except FileNotFoundError:
            pytest.skip("No database available")

    def test_set_db_path_with_valid_path(self, tmp_path):
        """Config.set_db_path() accepts valid path."""
        db_file = tmp_path / "custom.db"
        db_file.touch()

        Config.set_db_path(db_file)
        assert Config.get_db_path() == db_file

    def test_set_db_path_with_invalid_path(self):
        """Config.set_db_path() raises for nonexistent path."""
        with pytest.raises(FileNotFoundError):
            Config.set_db_path("/nonexistent/database.db")

    def test_reset_clears_cached_path(self, tmp_path):
        """Config.reset() clears the cached path."""
        db_file = tmp_path / "test.db"
        db_file.touch()

        Config.set_db_path(db_file)
        assert Config._db_path is not None

        Config.reset()
        assert Config._db_path is None

    def test_set_mode_to_http(self):
        """Config.set_mode("http") switches to http mode."""
        Config.set_mode("http")
        assert Config.get_mode() == "http"

    def test_set_api_url(self):
        """Config.set_api_url() sets the API URL."""
        Config.set_api_url("http://example.com:8333")
        assert Config.get_api_url() == "http://example.com:8333"
        assert Config.get_mode() == "http"


class TestDefaultPaths:
    """Tests for default configuration values."""

    def test_default_db_paths_are_pathlib_paths(self):
        """DEFAULT_DB_PATHS contains Path objects."""
        for path in DEFAULT_DB_PATHS:
            assert isinstance(path, Path)

    def test_default_api_urls_are_strings(self):
        """DEFAULT_API_URLS contains string URLs."""
        for url in DEFAULT_API_URLS:
            assert isinstance(url, str)
            assert url.startswith("http")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
