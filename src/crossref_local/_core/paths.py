"""Runtime state-directory resolver for crossref-local.

Lays out per-user runtime state under::

    $SCITEX_DIR/crossref-local/runtime/<sub>/

`$SCITEX_DIR` defaults to ``~/.scitex``. Anything outside ``runtime/``
is considered legacy and gets migrated on first import (see
:func:`_migrate_legacy_state`).
"""

from __future__ import annotations

import os as _os
from pathlib import Path as _Path

__all__ = [
    "scitex_dir",
    "package_dir",
    "runtime_dir",
    "state_dir",
]

_PKG_SHORT = "crossref-local"

# Subdirectories that historically lived directly under
# ~/.scitex/crossref-local/<sub>/ and now live under runtime/<sub>/.
# Used by the one-shot migration. Keep this conservative — only entries
# we know we own.
_KNOWN_SUBDIRS = (
    "cache",
    "db",
    "completion",
    "logs",
    "state",
)


def scitex_dir() -> _Path:
    """Return ``$SCITEX_DIR`` (default ``~/.scitex``) as a Path."""
    return _Path(_os.environ.get("SCITEX_DIR", _os.path.expanduser("~/.scitex")))


def package_dir() -> _Path:
    """``$SCITEX_DIR/crossref-local/`` — the package's top-level slot."""
    return scitex_dir() / _PKG_SHORT


def runtime_dir() -> _Path:
    """``$SCITEX_DIR/crossref-local/runtime/`` — all mutable state lives here."""
    return package_dir() / "runtime"


def state_dir(sub: str) -> _Path:
    """Return ``runtime/<sub>/`` and create it if missing.

    Parameters
    ----------
    sub : str
        Subdirectory name (e.g. ``"cache"``, ``"db"``).
    """
    d = runtime_dir() / sub
    d.mkdir(parents=True, exist_ok=True)
    return d


def _migrate_legacy_state() -> None:
    """Move legacy ``~/.scitex/crossref-local/<sub>/`` into ``runtime/<sub>/``.

    One-shot, best-effort. Only moves a subdir if:

    * OLD path exists,
    * NEW path does *not* exist (no overwrite),
    * the subdir name is in :data:`_KNOWN_SUBDIRS`.

    Never raises — callers wrap in try/except anyway.
    """
    pkg = package_dir()
    if not pkg.exists():
        return
    runtime = runtime_dir()
    runtime.mkdir(parents=True, exist_ok=True)
    for name in _KNOWN_SUBDIRS:
        old = pkg / name
        new = runtime / name
        if not old.exists() or old == runtime:
            continue
        # Skip if old is actually under runtime/ (already migrated, or
        # pkg == runtime which can't happen here but be safe).
        try:
            old.resolve().relative_to(runtime.resolve())
            continue
        except ValueError:
            pass
        if new.exists():
            # Don't clobber. Leave old in place; user can resolve.
            continue
        try:
            old.rename(new)
        except OSError:
            # Cross-device or perms — give up silently.
            continue


# EOF
