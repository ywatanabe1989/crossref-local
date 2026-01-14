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
            "search",
            "search_by_doi",
            "status",
        ]
        for tool_name in expected:
            assert tool_name in tools, f"Missing tool: {tool_name}"


class TestSearchTool:
    """Tests for search MCP tool."""

    def test_search_tool_exists(self):
        """search tool is registered."""
        assert "search" in mcp._tool_manager._tools

    def test_search_has_description(self):
        """search tool has description."""
        tool = mcp._tool_manager._tools["search"]
        assert tool.description is not None
        assert len(tool.description) > 0


class TestSearchByDoiTool:
    """Tests for search_by_doi MCP tool."""

    def test_search_by_doi_tool_exists(self):
        """search_by_doi tool is registered."""
        assert "search_by_doi" in mcp._tool_manager._tools


class TestStatusTool:
    """Tests for status MCP tool."""

    def test_status_tool_exists(self):
        """status tool is registered."""
        assert "status" in mcp._tool_manager._tools


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
