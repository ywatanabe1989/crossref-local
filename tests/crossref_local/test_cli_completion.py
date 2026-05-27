"""Tests for shell completion commands.

No mocks: ``$SHELL`` is managed by a yield-based env save/restore
fixture, and ``SHELL_CONFIGS`` is replaced by an explicit ``configs=``
DI seam on the production helpers — tests pass a dict whose values
are real ``tmp_path`` files.
"""

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from crossref_local._cli.completion import (
    BASH_COMPLETION,
    COMPLETION_END_MARKER,
    COMPLETION_MARKER,
    _detect_shell,
    _get_config_file,
    _install_completion,
    _is_installed,
    _uninstall_completion,
    completion,
)


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def temp_home(tmp_path):
    """Create a temporary home directory with shell config files."""
    bashrc = tmp_path / ".bashrc"
    bashrc.touch()
    zshrc = tmp_path / ".zshrc"
    zshrc.touch()
    fish_config = tmp_path / ".config" / "fish" / "config.fish"
    fish_config.parent.mkdir(parents=True)
    fish_config.touch()
    return tmp_path


@pytest.fixture
def shell_env():
    """Yield-based env save/restore for ``$SHELL``."""

    saved = os.environ.get("SHELL")
    had_saved = "SHELL" in os.environ

    def setter(value: str | None) -> None:
        if value is None:
            os.environ.pop("SHELL", None)
        else:
            os.environ["SHELL"] = value

    try:
        yield setter
    finally:
        if had_saved:
            os.environ["SHELL"] = saved  # type: ignore[arg-type]
        else:
            os.environ.pop("SHELL", None)


# ---------- _detect_shell ----------


def test_detect_shell_returns_bash_for_bin_bash(shell_env):
    # Arrange
    shell_env("/bin/bash")
    # Act
    detected = _detect_shell()
    # Assert
    assert detected == "bash"


def test_detect_shell_returns_zsh_for_usr_bin_zsh(shell_env):
    # Arrange
    shell_env("/usr/bin/zsh")
    # Act
    detected = _detect_shell()
    # Assert
    assert detected == "zsh"


def test_detect_shell_returns_fish_for_usr_local_bin_fish(shell_env):
    # Arrange
    shell_env("/usr/local/bin/fish")
    # Act
    detected = _detect_shell()
    # Assert
    assert detected == "fish"


def test_detect_shell_falls_back_to_bash_for_unknown_shell(shell_env):
    # Arrange
    shell_env("/bin/unknown")
    # Act
    detected = _detect_shell()
    # Assert
    assert detected == "bash"


def test_detect_shell_falls_back_to_bash_when_env_unset(shell_env):
    # Arrange
    shell_env(None)
    # Act
    detected = _detect_shell()
    # Assert
    assert detected == "bash"


# ---------- completion CLI surface ----------


def test_completion_help_exits_zero(runner):
    # Arrange
    args = ["--help"]
    # Act
    result = runner.invoke(completion, args)
    # Assert
    assert result.exit_code == 0


def test_completion_help_mentions_install_subcommand(runner):
    # Arrange
    args = ["--help"]
    # Act
    result = runner.invoke(completion, args)
    # Assert
    assert "install" in result.output


def test_completion_help_mentions_status_subcommand(runner):
    # Arrange
    args = ["--help"]
    # Act
    result = runner.invoke(completion, args)
    # Assert
    assert "status" in result.output


def test_completion_help_mentions_fish_subcommand(runner):
    # Arrange
    args = ["--help"]
    # Act
    result = runner.invoke(completion, args)
    # Assert
    assert "fish" in result.output


def test_completion_status_lists_bash_shell(runner):
    # Arrange
    args = ["status"]
    # Act
    result = runner.invoke(completion, args)
    # Assert
    assert "bash" in result.output


def test_completion_status_lists_zsh_shell(runner):
    # Arrange
    args = ["status"]
    # Act
    result = runner.invoke(completion, args)
    # Assert
    assert "zsh" in result.output


def test_completion_status_lists_fish_shell(runner):
    # Arrange
    args = ["status"]
    # Act
    result = runner.invoke(completion, args)
    # Assert
    assert "fish" in result.output


def test_completion_bash_subcommand_emits_bash_source_env(runner):
    # Arrange
    args = ["bash"]
    # Act
    result = runner.invoke(completion, args)
    # Assert
    assert "CROSSREF_LOCAL_COMPLETE=bash_source" in result.output


def test_completion_zsh_subcommand_emits_zsh_source_env(runner):
    # Arrange
    args = ["zsh"]
    # Act
    result = runner.invoke(completion, args)
    # Assert
    assert "CROSSREF_LOCAL_COMPLETE=zsh_source" in result.output


def test_completion_fish_subcommand_emits_fish_source_env(runner):
    # Arrange
    args = ["fish"]
    # Act
    result = runner.invoke(completion, args)
    # Assert
    assert "CROSSREF_LOCAL_COMPLETE=fish_source" in result.output


# ---------- _install_completion ----------


def test_install_completion_returns_success_for_fresh_bashrc(temp_home):
    # Arrange
    configs = {"bash": [temp_home / ".bashrc"]}
    # Act
    success, _ = _install_completion("bash", configs=configs)
    # Assert
    assert success is True


def test_install_completion_writes_completion_marker_into_bashrc(temp_home):
    # Arrange
    configs = {"bash": [temp_home / ".bashrc"]}
    # Act
    _install_completion("bash", configs=configs)
    content = (temp_home / ".bashrc").read_text()
    # Assert
    assert COMPLETION_MARKER in content


def test_install_completion_writes_end_marker_into_bashrc(temp_home):
    # Arrange
    configs = {"bash": [temp_home / ".bashrc"]}
    # Act
    _install_completion("bash", configs=configs)
    content = (temp_home / ".bashrc").read_text()
    # Assert
    assert COMPLETION_END_MARKER in content


def test_install_completion_writes_bash_eval_into_bashrc(temp_home):
    # Arrange
    configs = {"bash": [temp_home / ".bashrc"]}
    # Act
    _install_completion("bash", configs=configs)
    content = (temp_home / ".bashrc").read_text()
    # Assert
    assert "CROSSREF_LOCAL_COMPLETE=bash_source" in content


def test_install_completion_reports_already_installed_when_marker_present(
    temp_home,
):
    # Arrange
    bashrc = temp_home / ".bashrc"
    bashrc.write_text(f"{COMPLETION_MARKER}\ntest\n{COMPLETION_END_MARKER}\n")
    configs = {"bash": [bashrc]}
    # Act
    _, message = _install_completion("bash", configs=configs)
    # Assert
    assert "Already installed" in message


def test_install_completion_returns_failure_for_unknown_shell():
    # Arrange
    configs: dict[str, list[Path]] = {}
    # Act
    success, _ = _install_completion("unknown_shell", configs=configs)
    # Assert
    assert success is False


def test_install_completion_failure_message_describes_missing_config():
    # Arrange
    configs: dict[str, list[Path]] = {}
    # Act
    _, message = _install_completion("unknown_shell", configs=configs)
    # Assert
    assert "Could not find config file" in message


# ---------- _uninstall_completion ----------


def test_uninstall_completion_succeeds_when_block_present(temp_home):
    # Arrange
    bashrc = temp_home / ".bashrc"
    original = "# existing content\n"
    block = f"\n{COMPLETION_MARKER}\n{BASH_COMPLETION}{COMPLETION_END_MARKER}\n"
    bashrc.write_text(original + block + "# after\n")
    configs = {"bash": [bashrc]}
    # Act
    success, _ = _uninstall_completion("bash", configs=configs)
    # Assert
    assert success is True


def test_uninstall_completion_removes_marker_from_bashrc(temp_home):
    # Arrange
    bashrc = temp_home / ".bashrc"
    block = f"\n{COMPLETION_MARKER}\n{BASH_COMPLETION}{COMPLETION_END_MARKER}\n"
    bashrc.write_text("# existing content\n" + block + "# after\n")
    configs = {"bash": [bashrc]}
    # Act
    _uninstall_completion("bash", configs=configs)
    # Assert
    assert COMPLETION_MARKER not in bashrc.read_text()


def test_uninstall_completion_preserves_user_content_around_block(temp_home):
    # Arrange
    bashrc = temp_home / ".bashrc"
    block = f"\n{COMPLETION_MARKER}\n{BASH_COMPLETION}{COMPLETION_END_MARKER}\n"
    bashrc.write_text("# existing content\n" + block + "# after\n")
    configs = {"bash": [bashrc]}
    # Act
    _uninstall_completion("bash", configs=configs)
    # Assert
    assert "# existing content" in bashrc.read_text()


def test_uninstall_completion_reports_not_installed_when_marker_absent(temp_home):
    # Arrange
    bashrc = temp_home / ".bashrc"
    bashrc.write_text("# no completion installed\n")
    configs = {"bash": [bashrc]}
    # Act
    _, message = _uninstall_completion("bash", configs=configs)
    # Assert
    assert "Not installed" in message


# ---------- _is_installed ----------


def test_is_installed_returns_true_when_marker_present(temp_home):
    # Arrange
    bashrc = temp_home / ".bashrc"
    bashrc.write_text(f"{COMPLETION_MARKER}\ntest\n{COMPLETION_END_MARKER}\n")
    configs = {"bash": [bashrc]}
    # Act
    installed, _ = _is_installed("bash", configs=configs)
    # Assert
    assert installed is True


def test_is_installed_returns_matching_config_file_when_marker_present(temp_home):
    # Arrange
    bashrc = temp_home / ".bashrc"
    bashrc.write_text(f"{COMPLETION_MARKER}\ntest\n{COMPLETION_END_MARKER}\n")
    configs = {"bash": [bashrc]}
    # Act
    _, config_file = _is_installed("bash", configs=configs)
    # Assert
    assert config_file == bashrc


def test_is_installed_returns_false_when_marker_absent(temp_home):
    # Arrange
    bashrc = temp_home / ".bashrc"
    bashrc.write_text("# no completion\n")
    configs = {"bash": [bashrc]}
    # Act
    installed, _ = _is_installed("bash", configs=configs)
    # Assert
    assert installed is False


# ---------- _get_config_file ----------


def test_get_config_file_returns_existing_file_when_present(temp_home):
    # Arrange
    configs = {"bash": [temp_home / ".bashrc"]}
    # Act
    config = _get_config_file("bash", configs=configs)
    # Assert
    assert config == temp_home / ".bashrc"


def test_get_config_file_returns_first_candidate_when_none_exist(tmp_path):
    # Arrange
    nonexistent = tmp_path / ".nonexistent"
    configs = {"bash": [nonexistent]}
    # Act
    config = _get_config_file("bash", configs=configs)
    # Assert
    assert config == nonexistent
