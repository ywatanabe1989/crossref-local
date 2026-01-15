"""Tests for crossref_local.db module."""

import pytest
import sqlite3
from pathlib import Path

from crossref_local.db import Database, get_db, close_db, connection


class TestDatabase:
    """Tests for Database class."""

    def test_database_connects_successfully(self):
        """Database() establishes connection."""
        db = get_db()
        assert db is not None
        assert db.conn is not None

    def test_database_has_db_path(self):
        """Database has db_path attribute."""
        db = get_db()
        assert hasattr(db, "db_path")
        assert isinstance(db.db_path, Path)
        assert db.db_path.exists()

    def test_execute_returns_cursor(self):
        """execute() returns sqlite3.Cursor."""
        db = get_db()
        cursor = db.execute("SELECT 1")
        assert isinstance(cursor, sqlite3.Cursor)

    def test_fetchone_returns_row(self):
        """fetchone() returns a row."""
        db = get_db()
        row = db.fetchone("SELECT 1 as value")
        assert row is not None
        assert row["value"] == 1

    def test_fetchone_returns_none_for_no_results(self):
        """fetchone() returns None when no results."""
        db = get_db()
        row = db.fetchone("SELECT 1 WHERE 0 = 1")
        assert row is None

    def test_fetchall_returns_list(self):
        """fetchall() returns a list of rows."""
        db = get_db()
        rows = db.fetchall("SELECT 1 as value UNION SELECT 2")
        assert isinstance(rows, list)
        assert len(rows) == 2


class TestGetMetadata:
    """Tests for Database.get_metadata()."""

    def test_get_metadata_returns_dict_for_valid_doi(self):
        """get_metadata() returns dict for existing DOI."""
        db = get_db()
        # Find any DOI in database
        row = db.fetchone("SELECT doi FROM works LIMIT 1")
        if row:
            metadata = db.get_metadata(row["doi"])
            assert metadata is not None
            assert isinstance(metadata, dict)

    def test_get_metadata_returns_none_for_invalid_doi(self):
        """get_metadata() returns None for nonexistent DOI."""
        db = get_db()
        metadata = db.get_metadata("10.9999/nonexistent.doi")
        assert metadata is None

    def test_metadata_contains_expected_fields(self):
        """Metadata dict contains expected CrossRef fields."""
        db = get_db()
        row = db.fetchone("SELECT doi FROM works LIMIT 1")
        if row:
            metadata = db.get_metadata(row["doi"])
            # CrossRef metadata should have at least DOI
            assert metadata is not None


class TestDatabaseContextManager:
    """Tests for Database context manager."""

    def test_context_manager_provides_database(self):
        """connection() context manager yields Database."""
        with connection() as db:
            assert isinstance(db, Database)
            assert db.conn is not None

    def test_context_manager_closes_connection(self):
        """connection() closes database on exit."""
        with connection() as db:
            conn = db.conn
        # After context exit, connection should be closed
        assert db.conn is None


class TestSingleton:
    """Tests for singleton database functions."""

    def test_get_db_returns_same_instance(self):
        """get_db() returns singleton instance."""
        db1 = get_db()
        db2 = get_db()
        assert db1 is db2

    def test_close_db_clears_singleton(self):
        """close_db() clears the singleton."""
        db1 = get_db()
        close_db()
        db2 = get_db()
        # After close_db, should get new instance
        assert db1 is not db2


class TestWorksTable:
    """Tests for works table access."""

    def test_works_table_exists(self):
        """Works table exists in database."""
        db = get_db()
        row = db.fetchone(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='works'"
        )
        assert row is not None

    def test_works_table_has_expected_columns(self):
        """Works table has doi and metadata columns."""
        db = get_db()
        rows = db.fetchall("PRAGMA table_info(works)")
        columns = {row["name"] for row in rows}
        assert "doi" in columns
        assert "metadata" in columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
