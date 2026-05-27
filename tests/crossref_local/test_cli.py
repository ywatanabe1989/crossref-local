"""Tests for crossref_local.cli module."""

import json

import pytest
from click.testing import CliRunner

from crossref_local.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


# ---------- --help / --version surface ----------


def test_cli_main_help_exits_zero(runner):
    # Arrange
    args = ["--help"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_main_help_mentions_crossref_in_output(runner):
    # Arrange
    args = ["--help"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "crossref" in result.output.lower()


def test_cli_search_help_exits_zero(runner):
    # Arrange
    args = ["search", "--help"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_search_help_mentions_search_in_output(runner):
    # Arrange
    args = ["search", "--help"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "search" in result.output.lower()


def test_cli_search_by_doi_help_exits_zero(runner):
    # Arrange
    args = ["search-by-doi", "--help"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_search_by_doi_help_mentions_doi_in_output(runner):
    # Arrange
    args = ["search-by-doi", "--help"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "DOI" in result.output


def test_cli_status_help_exits_zero(runner):
    # Arrange
    args = ["status", "--help"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_version_flag_exits_zero(runner):
    # Arrange
    args = ["--version"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_version_flag_prints_package_name(runner):
    # Arrange
    args = ["--version"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "crossref-local" in result.output.lower()


def test_cli_help_recursive_exits_zero(runner):
    # Arrange
    args = ["--help-recursive"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_help_recursive_mentions_package_name(runner):
    # Arrange
    args = ["--help-recursive"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "crossref-local" in result.output


def test_cli_help_recursive_lists_search_subcommand(runner):
    # Arrange
    args = ["--help-recursive"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "search" in result.output


def test_cli_help_recursive_lists_status_subcommand(runner):
    # Arrange
    args = ["--help-recursive"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "status" in result.output


def test_cli_help_recursive_lists_search_by_doi_subcommand(runner):
    # Arrange
    args = ["--help-recursive"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "search-by-doi" in result.output


def test_cli_help_recursive_renders_formatted_separators(runner):
    # Arrange
    args = ["--help-recursive"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "━━━" in result.output


# ---------- search ----------


def test_cli_search_command_exits_zero_for_known_term(runner):
    # Arrange
    args = ["search", "cancer", "-n", "3"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_search_command_summarises_result_count_in_output(runner):
    # Arrange
    args = ["search", "cancer", "-n", "3"]
    # Act
    result = runner.invoke(cli, args)
    output = result.output.lower()
    # Assert
    assert ("matches" in output) or ("found" in output)


@pytest.fixture
def biology_search_json(runner):
    args = ["search", "biology", "-n", "2", "--json"]
    result = runner.invoke(cli, args)
    if result.exit_code != 0:
        pytest.skip(f"search command failed: {result.output!r}")
    return result, json.loads(result.output)


def test_cli_search_json_flag_exits_zero(biology_search_json):
    # Arrange
    result, _ = biology_search_json
    # Act
    code = result.exit_code
    # Assert
    assert code == 0


def test_cli_search_json_output_contains_query_key(biology_search_json):
    # Arrange
    _, data = biology_search_json
    # Act
    keys = data.keys()
    # Assert
    assert "query" in keys


def test_cli_search_json_output_contains_total_key(biology_search_json):
    # Arrange
    _, data = biology_search_json
    # Act
    keys = data.keys()
    # Assert
    assert "total" in keys


def test_cli_search_json_output_contains_works_key(biology_search_json):
    # Arrange
    _, data = biology_search_json
    # Act
    keys = data.keys()
    # Assert
    assert "works" in keys


def test_cli_search_n_limit_caps_works_array_length(runner):
    # Arrange
    args = ["search", "medicine", "-n", "5", "--json"]
    # Act
    result = runner.invoke(cli, args)
    if result.exit_code != 0:
        pytest.skip(f"search command failed: {result.output!r}")
    data = json.loads(result.output)
    # Assert
    assert len(data["works"]) <= 5


# ---------- search-by-doi ----------


def test_cli_search_by_doi_exits_nonzero_for_unknown_doi(runner):
    # Arrange
    args = ["search-by-doi", "10.9999/nonexistent"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 1


def test_cli_search_by_doi_reports_not_found_for_unknown_doi(runner):
    # Arrange
    args = ["search-by-doi", "10.9999/nonexistent"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "not found" in result.output.lower()


@pytest.fixture
def _real_doi_from_search(runner):
    args = ["search", "test", "-n", "1", "--json"]
    result = runner.invoke(cli, args)
    if result.exit_code != 0:
        pytest.skip("could not fetch a DOI to round-trip")
    data = json.loads(result.output)
    if not data["works"]:
        pytest.skip("no works returned by search")
    return data["works"][0]["doi"]


def test_cli_search_by_doi_json_output_contains_doi_key(
    runner, _real_doi_from_search
):
    # Arrange
    doi = _real_doi_from_search
    args = ["search-by-doi", doi, "--json"]
    # Act
    result = runner.invoke(cli, args)
    work = json.loads(result.output)
    # Assert
    assert "doi" in work


# ---------- status ----------


def test_cli_status_command_exits_zero(runner):
    # Arrange
    args = ["status"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_status_command_prints_status_label_in_output(runner):
    # Arrange
    args = ["status"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "status" in result.output.lower()


# ---------- relay ----------


def test_cli_relay_help_exits_zero(runner):
    # Arrange
    args = ["relay", "--help"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_relay_help_mentions_relay_or_port(runner):
    # Arrange
    args = ["relay", "--help"]
    # Act
    result = runner.invoke(cli, args)
    output = result.output.lower()
    # Assert
    assert ("relay" in output) or ("port" in output)


def test_cli_relay_dry_run_exits_zero(runner):
    # Arrange
    args = ["relay", "--dry-run"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_relay_dry_run_emits_dry_run_marker(runner):
    # Arrange
    args = ["relay", "--dry-run"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "[dry-run]" in result.output


# ---------- mcp ----------


def test_cli_mcp_help_exits_zero(runner):
    # Arrange
    args = ["mcp", "--help"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_mcp_help_lists_start_subcommand(runner):
    # Arrange
    args = ["mcp", "--help"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "start" in result.output


def test_cli_mcp_help_lists_doctor_subcommand(runner):
    # Arrange
    args = ["mcp", "--help"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "doctor" in result.output


def test_cli_mcp_start_dry_run_exits_zero(runner):
    # Arrange
    args = ["mcp", "start", "--dry-run"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert result.exit_code == 0


def test_cli_mcp_start_dry_run_emits_dry_run_marker(runner):
    # Arrange
    args = ["mcp", "start", "--dry-run"]
    # Act
    result = runner.invoke(cli, args)
    # Assert
    assert "[dry-run]" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
