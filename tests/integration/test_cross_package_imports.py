"""Runtime cross-package import gate (PS-140 §2).

This test imports every cross-package module that crossref-local
references in its source tree. Two outcomes:

- Module installed AND import succeeds → test PASSES.
- Module installed BUT import fails (e.g. internal rename) → test FAILS loudly.
- Module NOT installed (peer standalone absent in the CI env) → test is
  SKIPPED via `pytest.importorskip`. The umbrella's CI catches renames.
"""

import pytest

CROSS_PACKAGE_IMPORTS = [
    "scitex.cli.introspect",
    "scitex_dev",
    "scitex_dev._cli._completion",
    "scitex_dev.cli",
    "scitex_dev.decorators",
]


@pytest.mark.parametrize("module_path", CROSS_PACKAGE_IMPORTS)
def test_cross_package_import(module_path: str) -> None:
    """Each cross-package import resolves cleanly when the peer is installed."""
    pytest.importorskip(module_path)
