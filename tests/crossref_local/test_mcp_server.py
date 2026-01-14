"""Tests for crossref_local.mcp_server module."""

import json
import pytest

from crossref_local.mcp_server import mcp


class TestMCPServerSetup:
    """Tests for MCP server configuration."""

    def test_mcp_server_has_name(self):
        """MCP server has a name."""
        assert mcp.name == "crossref-local"

    def test_mcp_server_has_tools(self):
        """MCP server has registered tools."""
        tools = list(mcp._tool_manager._tools.keys())
        assert len(tools) > 0

    def test_expected_tools_registered(self):
        """Expected tools are registered."""
        tools = list(mcp._tool_manager._tools.keys())
        expected = [
            "search_works",
            "get_work",
            "count_works",
            "database_info",
            "calculate_impact_factor",
        ]
        for tool_name in expected:
            assert tool_name in tools, f"Missing tool: {tool_name}"


class TestSearchWorksTool:
    """Tests for search_works MCP tool."""

    def test_search_works_tool_exists(self):
        """search_works tool is registered."""
        assert "search_works" in mcp._tool_manager._tools

    def test_search_works_has_description(self):
        """search_works tool has description."""
        tool = mcp._tool_manager._tools["search_works"]
        assert tool.description is not None
        assert len(tool.description) > 0


class TestGetWorkTool:
    """Tests for get_work MCP tool."""

    def test_get_work_tool_exists(self):
        """get_work tool is registered."""
        assert "get_work" in mcp._tool_manager._tools


class TestCountWorksTool:
    """Tests for count_works MCP tool."""

    def test_count_works_tool_exists(self):
        """count_works tool is registered."""
        assert "count_works" in mcp._tool_manager._tools


class TestDatabaseInfoTool:
    """Tests for database_info MCP tool."""

    def test_database_info_tool_exists(self):
        """database_info tool is registered."""
        assert "database_info" in mcp._tool_manager._tools


class TestCalculateImpactFactorTool:
    """Tests for calculate_impact_factor MCP tool."""

    def test_calculate_impact_factor_tool_exists(self):
        """calculate_impact_factor tool is registered."""
        assert "calculate_impact_factor" in mcp._tool_manager._tools


class TestRunServer:
    """Tests for run_server function."""

    def test_run_server_import(self):
        """run_server can be imported."""
        from crossref_local.mcp_server import run_server

        assert callable(run_server)

    def test_main_import(self):
        """main entry point can be imported."""
        from crossref_local.mcp_server import main

        assert callable(main)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
