"""Tests for crossref_local.mcp_server module."""

import asyncio

import pytest

# PA-303: fastmcp is in [mcp]/[dev] extras, not [project] dependencies.
# `crossref_local.mcp_server` re-exports from `._cli.mcp_server`, which
# does `from fastmcp import FastMCP` at module top.
fastmcp = pytest.importorskip("fastmcp")

from crossref_local.mcp_server import mcp


@pytest.fixture
def tools_by_name():
    """Snapshot of registered MCP tools, keyed by name."""
    tools = asyncio.run(mcp.list_tools())
    return {t.name: t for t in tools}


# ---------- server identity ----------


def test_mcp_server_name_matches_package_distribution_name():
    # Arrange
    server = mcp
    # Act
    name = server.name
    # Assert
    assert name == "crossref-local"


def test_mcp_server_registers_at_least_one_tool(tools_by_name):
    # Arrange
    # Act
    count = len(tools_by_name)
    # Assert
    assert count > 0


# ---------- expected tools registered ----------


def test_mcp_server_registers_search_works_tool(tools_by_name):
    # Arrange
    # Act
    present = "search_works" in tools_by_name
    # Assert
    assert present


def test_mcp_server_registers_search_by_doi_tool(tools_by_name):
    # Arrange
    # Act
    present = "search_by_doi" in tools_by_name
    # Assert
    assert present


def test_mcp_server_registers_get_status_tool(tools_by_name):
    # Arrange
    # Act
    present = "get_status" in tools_by_name
    # Assert
    assert present


# ---------- search_works metadata ----------


def test_mcp_search_works_tool_has_nonempty_description(tools_by_name):
    # Arrange
    tool = tools_by_name["search_works"]
    # Act
    desc = tool.description or ""
    # Assert
    assert len(desc) > 0


# ---------- run_server / main entry-points ----------


def test_run_server_module_attribute_is_callable():
    # Arrange
    from crossref_local.mcp_server import run_server

    # Act
    is_callable = callable(run_server)
    # Assert
    assert is_callable


def test_main_module_attribute_is_callable():
    # Arrange
    from crossref_local.mcp_server import main

    # Act
    is_callable = callable(main)
    # Assert
    assert is_callable


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
