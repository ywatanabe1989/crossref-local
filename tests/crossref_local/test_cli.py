"""Tests for crossref_local.cli module."""

import json
import pytest
from click.testing import CliRunner

from crossref_local.cli import cli


@pytest.fixture
def runner():
    """Create CLI test runner."""
    return CliRunner()


class TestCLIHelp:
    """Tests for CLI help commands."""

    def test_main_help(self, runner):
        """Main CLI shows help."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "CrossRef" in result.output or "crossref" in result.output.lower()

    def test_search_help(self, runner):
        """search command shows help."""
        result = runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "Search" in result.output or "search" in result.output.lower()

    def test_search_by_doi_help(self, runner):
        """search-by-doi command shows help."""
        result = runner.invoke(cli, ["search-by-doi", "--help"])
        assert result.exit_code == 0
        assert "DOI" in result.output

    def test_status_help(self, runner):
        """status command shows help."""
        result = runner.invoke(cli, ["status", "--help"])
        assert result.exit_code == 0

    def test_version(self, runner):
        """--version shows version."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "crossref-local" in result.output.lower()

    def test_help_recursive(self, runner):
        """--help-recursive shows help for all commands."""
        result = runner.invoke(cli, ["--help-recursive"])
        assert result.exit_code == 0
        # Check main header
        assert "crossref-local" in result.output
        # Check all subcommands are included
        assert "search" in result.output
        assert "status" in result.output
        assert "run-server-mcp" in result.output
        assert "run-server-http" in result.output
        assert "search-by-doi" in result.output
        # Check formatted separators are present
        assert "━━━" in result.output


class TestSearchCommand:
    """Tests for search command."""

    def test_search_basic(self, runner):
        """search returns results."""
        result = runner.invoke(cli, ["search", "cancer", "-n", "3"])
        assert result.exit_code == 0
        assert "matches" in result.output.lower() or "found" in result.output.lower()

    def test_search_json_output(self, runner):
        """search --json returns valid JSON."""
        result = runner.invoke(cli, ["search", "biology", "-n", "2", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "query" in data
        assert "total" in data
        assert "works" in data

    def test_search_with_limit(self, runner):
        """search -n limits results."""
        result = runner.invoke(cli, ["search", "medicine", "-n", "5", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert len(data["works"]) <= 5


class TestSearchByDoiCommand:
    """Tests for search-by-doi command."""

    def test_search_by_doi_nonexistent(self, runner):
        """search-by-doi returns error for nonexistent DOI."""
        result = runner.invoke(cli, ["search-by-doi", "10.9999/nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_search_by_doi_json_output(self, runner):
        """search-by-doi --json returns valid JSON."""
        # First find a valid DOI
        search_result = runner.invoke(cli, ["search", "test", "-n", "1", "--json"])
        if search_result.exit_code == 0:
            data = json.loads(search_result.output)
            if data["works"]:
                doi = data["works"][0]["doi"]
                result = runner.invoke(cli, ["search-by-doi", doi, "--json"])
                assert result.exit_code == 0
                work_data = json.loads(result.output)
                assert "doi" in work_data


class TestStatusCommand:
    """Tests for status command."""

    def test_status_basic(self, runner):
        """status shows configuration status."""
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "Status" in result.output or "status" in result.output.lower()


class TestRunServerMcpCommand:
    """Tests for run-server-mcp command."""

    def test_run_server_mcp_help(self, runner):
        """run-server-mcp --help shows MCP server options."""
        result = runner.invoke(cli, ["run-server-mcp", "--help"])
        assert result.exit_code == 0
        assert "MCP" in result.output or "transport" in result.output.lower()


class TestRunServerHttpCommand:
    """Tests for run-server-http command."""

    def test_run_server_http_help(self, runner):
        """run-server-http --help shows HTTP server options."""
        result = runner.invoke(cli, ["run-server-http", "--help"])
        assert result.exit_code == 0
        assert "HTTP" in result.output or "port" in result.output.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
