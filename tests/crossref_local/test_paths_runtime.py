"""Sanity tests for the runtime state-dir separation pattern.

Verifies that:

* ``import crossref_local`` doesn't raise.
* ``_core.paths.state_dir(<sub>)`` lands under ``runtime/<sub>/``.
* ``_migrate_legacy_state`` moves a known legacy subdir to runtime/.
"""

from __future__ import annotations

import os

import pytest


@pytest.fixture
def scitex_dir_env(tmp_path):
    """Point ``$SCITEX_DIR`` at a real, throw-away tmp_path.

    Sets the env var directly (no monkeypatch) and restores the prior
    value on teardown. Yields the path so the test can compare.
    """
    # Arrange
    prev = os.environ.get("SCITEX_DIR")
    os.environ["SCITEX_DIR"] = str(tmp_path)
    try:
        yield tmp_path
    finally:
        if prev is None:
            os.environ.pop("SCITEX_DIR", None)
        else:
            os.environ["SCITEX_DIR"] = prev


def test_import_does_not_break():
    """Import must succeed with .env-respect + migration hooks active."""
    # Arrange
    import importlib

    # Act
    mod = importlib.import_module("crossref_local")

    # Assert
    assert hasattr(mod, "search")


def test_state_dir_resolves_under_runtime(scitex_dir_env):
    """``state_dir("cache")`` must resolve under ``runtime/cache``."""
    # Arrange
    from crossref_local._core import paths

    expected = scitex_dir_env / "crossref-local" / "runtime" / "cache"

    # Act
    cache = paths.state_dir("cache")

    # Assert
    assert cache == expected


def test_state_dir_creates_directory(scitex_dir_env):
    """``state_dir`` must create the resolved path on disk."""
    # Arrange
    from crossref_local._core import paths

    # Act
    cache = paths.state_dir("cache")

    # Assert
    assert cache.is_dir()


def test_runtime_dir_under_package_dir(scitex_dir_env):
    """``runtime_dir`` must be ``package_dir / "runtime"``."""
    # Arrange
    from crossref_local._core import paths

    # Act
    rt = paths.runtime_dir()

    # Assert
    assert rt == paths.package_dir() / "runtime"


def test_package_dir_uses_scitex_dir_env(scitex_dir_env):
    """``package_dir`` must honour ``$SCITEX_DIR``."""
    # Arrange
    from crossref_local._core import paths

    # Act
    pkg = paths.package_dir()

    # Assert
    assert pkg == scitex_dir_env / "crossref-local"


def test_migrate_legacy_state_moves_known_subdir(scitex_dir_env):
    """Legacy ``~/.scitex/crossref-local/<sub>/`` -> ``runtime/<sub>/``."""
    # Arrange
    from crossref_local._core import paths

    pkg = paths.package_dir()
    pkg.mkdir(parents=True, exist_ok=True)
    legacy = pkg / "cache"
    legacy.mkdir()
    (legacy / "marker.txt").write_text("old")

    # Act
    paths._migrate_legacy_state()

    # Assert
    assert (pkg / "runtime" / "cache" / "marker.txt").read_text() == "old"


def test_migrate_legacy_state_removes_old_dir(scitex_dir_env):
    """After migration, the legacy sibling of runtime/ is gone."""
    # Arrange
    from crossref_local._core import paths

    pkg = paths.package_dir()
    pkg.mkdir(parents=True, exist_ok=True)
    legacy = pkg / "cache"
    legacy.mkdir()
    (legacy / "marker.txt").write_text("old")

    # Act
    paths._migrate_legacy_state()

    # Assert
    assert not legacy.exists()


def test_migrate_does_not_clobber_existing_runtime(scitex_dir_env):
    """If runtime/<sub>/ already exists, the new file is preserved."""
    # Arrange
    from crossref_local._core import paths

    pkg = paths.package_dir()
    (pkg / "cache").mkdir(parents=True)
    (pkg / "cache" / "old.txt").write_text("legacy")
    (pkg / "runtime" / "cache").mkdir(parents=True)
    (pkg / "runtime" / "cache" / "new.txt").write_text("modern")

    # Act
    paths._migrate_legacy_state()

    # Assert
    assert (pkg / "runtime" / "cache" / "new.txt").read_text() == "modern"


def test_migrate_does_not_clobber_keeps_legacy(scitex_dir_env):
    """If runtime/<sub>/ already exists, the legacy dir stays put."""
    # Arrange
    from crossref_local._core import paths

    pkg = paths.package_dir()
    legacy = pkg / "cache"
    legacy.mkdir(parents=True)
    (legacy / "old.txt").write_text("legacy")
    (pkg / "runtime" / "cache").mkdir(parents=True)

    # Act
    paths._migrate_legacy_state()

    # Assert
    assert (legacy / "old.txt").read_text() == "legacy"


# EOF
