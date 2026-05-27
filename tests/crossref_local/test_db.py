"""Tests for crossref_local.db module."""

import sqlite3
from pathlib import Path

import pytest

from crossref_local._core.db import (
    Database,
    close_db,
    connection,
    get_db,
)


@pytest.fixture
def db():
    """Singleton Database handle for the test session DB."""
    return get_db()


# ---------- Database singleton ----------


def test_get_db_returns_non_none_database_handle(db):
    # Arrange
    # Act
    handle = db
    # Assert
    assert handle is not None


def test_get_db_handle_has_open_sqlite_connection(db):
    # Arrange
    # Act
    conn = db.conn
    # Assert
    assert conn is not None


def test_get_db_handle_exposes_db_path_attribute(db):
    # Arrange
    # Act
    has_attr = hasattr(db, "db_path")
    # Assert
    assert has_attr


def test_get_db_handle_db_path_is_pathlib_path(db):
    # Arrange
    # Act
    path = db.db_path
    # Assert
    assert isinstance(path, Path)


def test_get_db_handle_db_path_exists_on_disk(db):
    # Arrange
    path = db.db_path
    # Act
    present = path.exists()
    # Assert
    assert present


# ---------- execute / fetchone / fetchall ----------


def test_database_execute_returns_sqlite_cursor_instance(db):
    # Arrange
    # Act
    cursor = db.execute("SELECT 1")
    # Assert
    assert isinstance(cursor, sqlite3.Cursor)


def test_database_fetchone_returns_row_for_matching_query(db):
    # Arrange
    sql = "SELECT 1 as value"
    # Act
    row = db.fetchone(sql)
    # Assert
    assert row is not None


def test_database_fetchone_row_supports_column_indexing_by_name(db):
    # Arrange
    sql = "SELECT 1 as value"
    # Act
    row = db.fetchone(sql)
    # Assert
    assert row["value"] == 1


def test_database_fetchone_returns_none_when_no_rows_match(db):
    # Arrange
    sql = "SELECT 1 WHERE 0 = 1"
    # Act
    row = db.fetchone(sql)
    # Assert
    assert row is None


def test_database_fetchall_returns_list_instance(db):
    # Arrange
    sql = "SELECT 1 as value UNION SELECT 2"
    # Act
    rows = db.fetchall(sql)
    # Assert
    assert isinstance(rows, list)


def test_database_fetchall_returns_one_row_per_union_branch(db):
    # Arrange
    sql = "SELECT 1 as value UNION SELECT 2"
    # Act
    rows = db.fetchall(sql)
    # Assert
    assert len(rows) == 2


# ---------- get_metadata ----------


@pytest.fixture
def any_existing_doi(db):
    """A real DOI from the test DB, or skip if the DB has none."""
    row = db.fetchone("SELECT doi FROM works LIMIT 1")
    if row is None:
        pytest.skip("test DB contains no works")
    return row["doi"]


def test_get_metadata_returns_dict_for_doi_present_in_database(
    db, any_existing_doi
):
    # Arrange
    doi = any_existing_doi
    # Act
    metadata = db.get_metadata(doi)
    # Assert
    assert isinstance(metadata, dict)


def test_get_metadata_returns_none_for_doi_not_present_in_database(db):
    # Arrange
    doi = "10.9999/nonexistent.doi"
    # Act
    metadata = db.get_metadata(doi)
    # Assert
    assert metadata is None


def test_get_metadata_returns_truthy_payload_for_known_doi(
    db, any_existing_doi
):
    # Arrange
    doi = any_existing_doi
    # Act
    metadata = db.get_metadata(doi)
    # Assert
    assert metadata is not None


# ---------- connection() context manager ----------


def test_connection_context_yields_database_instance():
    # Arrange
    # Act
    with connection() as db:
        is_db = isinstance(db, Database)
    # Assert
    assert is_db


def test_connection_context_provides_open_sqlite_connection():
    # Arrange
    # Act
    with connection() as db:
        conn = db.conn
    # Assert
    assert conn is not None


def test_connection_context_closes_handle_on_exit():
    # Arrange
    with connection() as db:
        pass
    # Act
    conn = db.conn
    # Assert
    assert conn is None


# ---------- get_db / close_db singleton semantics ----------


def test_get_db_returns_same_instance_on_repeat_call():
    # Arrange
    first = get_db()
    # Act
    second = get_db()
    # Assert
    assert first is second


def test_close_db_drops_singleton_so_next_get_db_is_fresh():
    # Arrange
    first = get_db()
    # Act
    close_db()
    second = get_db()
    # Assert
    assert first is not second


# ---------- schema sanity ----------


def test_database_schema_includes_a_works_table(db):
    # Arrange
    sql = "SELECT name FROM sqlite_master WHERE type='table' AND name='works'"
    # Act
    row = db.fetchone(sql)
    # Assert
    assert row is not None


def test_works_table_has_doi_column(db):
    # Arrange
    rows = db.fetchall("PRAGMA table_info(works)")
    # Act
    columns = {row["name"] for row in rows}
    # Assert
    assert "doi" in columns


def test_works_table_has_metadata_column(db):
    # Arrange
    rows = db.fetchall("PRAGMA table_info(works)")
    # Act
    columns = {row["name"] for row in rows}
    # Assert
    assert "metadata" in columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
