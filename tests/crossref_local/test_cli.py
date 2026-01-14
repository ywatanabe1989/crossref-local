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

    def test_get_help(self, runner):
        """get command shows help."""
        result = runner.invoke(cli, ["get", "--help"])
        assert result.exit_code == 0
        assert "DOI" in result.output

    def test_count_help(self, runner):
        """count command shows help."""
        result = runner.invoke(cli, ["count", "--help"])
        assert result.exit_code == 0

    def test_info_help(self, runner):
        """info command shows help."""
        result = runner.invoke(cli, ["info", "--help"])
        assert result.exit_code == 0

    def test_version(self, runner):
        """--version shows version."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "crossref-local" in result.output.lower()


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

    def test_search_alias_s(self, runner):
        """s alias works for search."""
        result = runner.invoke(cli, ["s", "physics", "-n", "1"])
        assert result.exit_code == 0


class TestGetCommand:
    """Tests for get command."""

    def test_get_nonexistent_doi(self, runner):
        """get returns error for nonexistent DOI."""
        result = runner.invoke(cli, ["get", "10.9999/nonexistent"])
        assert result.exit_code == 1
        assert "not found" in result.output.lower()

    def test_get_json_output(self, runner):
        """get --json returns valid JSON."""
        # First find a valid DOI
        search_result = runner.invoke(cli, ["search", "test", "-n", "1", "--json"])
        if search_result.exit_code == 0:
            data = json.loads(search_result.output)
            if data["works"]:
                doi = data["works"][0]["doi"]
                result = runner.invoke(cli, ["get", doi, "--json"])
                assert result.exit_code == 0
                work_data = json.loads(result.output)
                assert "doi" in work_data

    def test_get_alias_g(self, runner):
        """g alias works for get."""
        result = runner.invoke(cli, ["g", "10.9999/nonexistent"])
        assert result.exit_code == 1  # Expected - DOI doesn't exist


class TestCountCommand:
    """Tests for count command."""

    def test_count_basic(self, runner):
        """count returns a number."""
        result = runner.invoke(cli, ["count", "cancer"])
        assert result.exit_code == 0
        # Output should be a number (with commas for formatting)
        count_str = result.output.strip().replace(",", "")
        assert count_str.isdigit()

    def test_count_alias_c(self, runner):
        """c alias works for count."""
        result = runner.invoke(cli, ["c", "biology"])
        assert result.exit_code == 0


class TestInfoCommand:
    """Tests for info command."""

    def test_info_basic(self, runner):
        """info shows database information."""
        result = runner.invoke(cli, ["info"])
        assert result.exit_code == 0
        assert "Works" in result.output or "works" in result.output.lower()

    def test_info_json_output(self, runner):
        """info --json returns valid JSON."""
        result = runner.invoke(cli, ["info", "--json"])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "works" in data or "total_papers" in data

    def test_info_alias_i(self, runner):
        """i alias works for info."""
        result = runner.invoke(cli, ["i"])
        assert result.exit_code == 0


class TestSetupCommand:
    """Tests for setup command."""

    def test_setup_shows_status(self, runner):
        """setup shows configuration status."""
        result = runner.invoke(cli, ["setup"])
        assert result.exit_code == 0
        assert "Setup" in result.output or "setup" in result.output.lower()


class TestServeCommand:
    """Tests for serve command."""

    def test_serve_help(self, runner):
        """serve --help shows MCP server options."""
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "MCP" in result.output or "Claude" in result.output


class TestApiCommand:
    """Tests for api command."""

    def test_api_help(self, runner):
        """api --help shows HTTP server options."""
        result = runner.invoke(cli, ["api", "--help"])
        assert result.exit_code == 0
        assert "HTTP" in result.output or "FastAPI" in result.output or "port" in result.output.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
