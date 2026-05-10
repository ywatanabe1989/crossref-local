"""Tests for crossref_local.mcp_server module."""

import asyncio

import pytest

from crossref_local.mcp_server import mcp


def _get_tools():
    """Get tools dict from FastMCP v2."""
    tools = asyncio.run(mcp.list_tools())
    return {t.name: t for t in tools}


class TestMCPServerSetup:
    """Tests for MCP server configuration."""

    def test_mcp_server_has_name(self):
        """MCP server has a name."""
        assert mcp.name == "crossref-local"

    def test_mcp_server_has_tools(self):
        """MCP server has registered tools."""
        tools = _get_tools()
        assert len(tools) > 0

    def test_expected_tools_registered(self):
        """Expected tools are registered. Names follow the §3 verb_noun
        rule — `search` was renamed to `search_works`, `status` to
        `get_status` (both via `@mcp.tool(name=...)` overrides)."""
        tools = _get_tools()
        expected = ["search_works", "search_by_doi", "get_status"]
        for tool_name in expected:
            assert tool_name in tools, f"Missing tool: {tool_name}"


class TestSearchTool:
    """Tests for `search_works` MCP tool (registered name; the
    underlying function is still `search`)."""

    def test_search_tool_exists(self):
        """search_works tool is registered."""
        assert "search_works" in _get_tools()

    def test_search_has_description(self):
        """search_works tool has description."""
        tool = _get_tools()["search_works"]
        assert tool.description is not None
        assert len(tool.description) > 0


class TestSearchByDoiTool:
    """Tests for search_by_doi MCP tool."""

    def test_search_by_doi_tool_exists(self):
        """search_by_doi tool is registered."""
        assert "search_by_doi" in _get_tools()


class TestStatusTool:
    """Tests for `get_status` MCP tool (registered name; the
    underlying function is still `status`)."""

    def test_status_tool_exists(self):
        """get_status tool is registered."""
        assert "get_status" in _get_tools()


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
