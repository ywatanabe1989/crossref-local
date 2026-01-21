"""Tests for shell completion commands."""

import os
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from crossref_local.cli_completion import (
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


class TestDetectShell:
    def test_detect_bash(self):
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}):
            assert _detect_shell() == "bash"

    def test_detect_zsh(self):
        with patch.dict(os.environ, {"SHELL": "/usr/bin/zsh"}):
            assert _detect_shell() == "zsh"

    def test_detect_fish(self):
        with patch.dict(os.environ, {"SHELL": "/usr/local/bin/fish"}):
            assert _detect_shell() == "fish"

    def test_detect_fallback_bash(self):
        with patch.dict(os.environ, {"SHELL": "/bin/unknown"}):
            assert _detect_shell() == "bash"

    def test_detect_no_shell(self):
        with patch.dict(os.environ, {}, clear=True):
            assert _detect_shell() == "bash"


class TestCompletionHelp:
    def test_completion_help(self, runner):
        result = runner.invoke(completion, ["--help"])
        assert result.exit_code == 0
        assert "Shell completion commands" in result.output
        assert "install" in result.output
        assert "status" in result.output
        assert "bash" in result.output
        assert "zsh" in result.output
        assert "fish" in result.output


class TestCompletionStatus:
    def test_status_shows_all_shells(self, runner):
        result = runner.invoke(completion, ["status"])
        assert result.exit_code == 0
        assert "bash" in result.output
        assert "zsh" in result.output
        assert "fish" in result.output


class TestCompletionScripts:
    def test_bash_script(self, runner):
        result = runner.invoke(completion, ["bash"])
        assert result.exit_code == 0
        assert "CROSSREF_LOCAL_COMPLETE=bash_source" in result.output

    def test_zsh_script(self, runner):
        result = runner.invoke(completion, ["zsh"])
        assert result.exit_code == 0
        assert "CROSSREF_LOCAL_COMPLETE=zsh_source" in result.output

    def test_fish_script(self, runner):
        result = runner.invoke(completion, ["fish"])
        assert result.exit_code == 0
        assert "CROSSREF_LOCAL_COMPLETE=fish_source" in result.output


class TestInstallCompletion:
    def test_install_bash(self, temp_home):
        with patch(
            "crossref_local.cli_completion.SHELL_CONFIGS",
            {"bash": [temp_home / ".bashrc"]},
        ):
            success, message = _install_completion("bash")
            assert success
            assert "Installed" in message

            # Verify content
            content = (temp_home / ".bashrc").read_text()
            assert COMPLETION_MARKER in content
            assert COMPLETION_END_MARKER in content
            assert "CROSSREF_LOCAL_COMPLETE=bash_source" in content

    def test_install_already_installed(self, temp_home):
        bashrc = temp_home / ".bashrc"
        bashrc.write_text(f"{COMPLETION_MARKER}\ntest\n{COMPLETION_END_MARKER}\n")

        with patch(
            "crossref_local.cli_completion.SHELL_CONFIGS",
            {"bash": [bashrc]},
        ):
            success, message = _install_completion("bash")
            assert success
            assert "Already installed" in message

    def test_install_unsupported_shell(self):
        success, message = _install_completion("unknown_shell")
        assert not success
        assert "Could not find config file" in message


class TestUninstallCompletion:
    def test_uninstall_bash(self, temp_home):
        bashrc = temp_home / ".bashrc"
        original = "# existing content\n"
        completion_block = (
            f"\n{COMPLETION_MARKER}\n{BASH_COMPLETION}{COMPLETION_END_MARKER}\n"
        )
        bashrc.write_text(original + completion_block + "# after\n")

        with patch(
            "crossref_local.cli_completion.SHELL_CONFIGS",
            {"bash": [bashrc]},
        ):
            success, message = _uninstall_completion("bash")
            assert success
            assert "Removed" in message

            content = bashrc.read_text()
            assert COMPLETION_MARKER not in content
            assert "# existing content" in content

    def test_uninstall_not_installed(self, temp_home):
        bashrc = temp_home / ".bashrc"
        bashrc.write_text("# no completion installed\n")

        with patch(
            "crossref_local.cli_completion.SHELL_CONFIGS",
            {"bash": [bashrc]},
        ):
            success, message = _uninstall_completion("bash")
            assert success
            assert "Not installed" in message


class TestIsInstalled:
    def test_is_installed_true(self, temp_home):
        bashrc = temp_home / ".bashrc"
        bashrc.write_text(f"{COMPLETION_MARKER}\ntest\n{COMPLETION_END_MARKER}\n")

        with patch(
            "crossref_local.cli_completion.SHELL_CONFIGS",
            {"bash": [bashrc]},
        ):
            installed, config_file = _is_installed("bash")
            assert installed
            assert config_file == bashrc

    def test_is_installed_false(self, temp_home):
        bashrc = temp_home / ".bashrc"
        bashrc.write_text("# no completion\n")

        with patch(
            "crossref_local.cli_completion.SHELL_CONFIGS",
            {"bash": [bashrc]},
        ):
            installed, config_file = _is_installed("bash")
            assert not installed


class TestGetConfigFile:
    def test_get_existing_config(self, temp_home):
        with patch(
            "crossref_local.cli_completion.SHELL_CONFIGS",
            {"bash": [temp_home / ".bashrc"]},
        ):
            config = _get_config_file("bash")
            assert config == temp_home / ".bashrc"

    def test_get_first_option_if_none_exist(self, tmp_path):
        nonexistent = tmp_path / ".nonexistent"
        with patch(
            "crossref_local.cli_completion.SHELL_CONFIGS",
            {"bash": [nonexistent]},
        ):
            config = _get_config_file("bash")
            assert config == nonexistent
