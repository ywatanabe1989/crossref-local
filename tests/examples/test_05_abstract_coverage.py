"""Compile-only smoke for examples/05_abstract_coverage.py (PS303)."""

import subprocess
import sys
from pathlib import Path

EXAMPLE = Path(__file__).resolve().parents[2] / "examples" / "05_abstract_coverage.py"


def test_abstract_coverage_example_file_exists_on_disk():
    # Arrange
    target = EXAMPLE
    # Act
    present = target.exists()
    # Assert
    assert present, f"missing example: {target}"


def test_abstract_coverage_example_compiles_with_py_compile_cleanly():
    # Arrange
    cmd = [sys.executable, "-m", "py_compile", str(EXAMPLE)]
    # Act
    completed = subprocess.run(cmd, check=False, capture_output=True)
    # Assert
    assert completed.returncode == 0, completed.stderr.decode()
