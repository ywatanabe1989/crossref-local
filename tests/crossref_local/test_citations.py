"""Tests for crossref_local.citations module."""

import pytest

from crossref_local._core.citations import (
    CitationEdge,
    CitationNetwork,
    CitationNode,
    get_citation_count,
    get_cited,
    get_citing,
)


# ---------- get_citing ----------


def test_get_citing_returns_list_instance_for_sample_doi(sample_doi):
    # Arrange
    # Act
    citing = get_citing(sample_doi)
    # Assert
    assert isinstance(citing, list)


def test_get_citing_returns_only_string_dois_for_sample_doi(sample_doi):
    # Arrange
    # Act
    citing = get_citing(sample_doi, limit=5)
    # Assert
    assert all(isinstance(d, str) for d in citing)


def test_get_citing_respects_limit_argument(sample_doi):
    # Arrange
    limit = 3
    # Act
    citing = get_citing(sample_doi, limit=limit)
    # Assert
    assert len(citing) <= limit


def test_get_citing_returns_empty_list_for_unknown_doi():
    # Arrange
    # Act
    citing = get_citing("10.0000/nonexistent")
    # Assert
    assert citing == []


# ---------- get_cited ----------


def test_get_cited_returns_list_instance_for_sample_doi(sample_doi):
    # Arrange
    # Act
    cited = get_cited(sample_doi)
    # Assert
    assert isinstance(cited, list)


def test_get_cited_returns_only_string_dois_for_sample_doi(sample_doi):
    # Arrange
    # Act
    cited = get_cited(sample_doi, limit=5)
    # Assert
    assert all(isinstance(d, str) for d in cited)


def test_get_cited_respects_limit_argument(sample_doi):
    # Arrange
    limit = 3
    # Act
    cited = get_cited(sample_doi, limit=limit)
    # Assert
    assert len(cited) <= limit


def test_get_cited_returns_empty_list_for_unknown_doi():
    # Arrange
    # Act
    cited = get_cited("10.0000/nonexistent")
    # Assert
    assert cited == []


# ---------- get_citation_count ----------


def test_get_citation_count_returns_integer_type_for_sample_doi(sample_doi):
    # Arrange
    # Act
    n = get_citation_count(sample_doi)
    # Assert
    assert isinstance(n, int)


def test_get_citation_count_returns_nonnegative_for_sample_doi(sample_doi):
    # Arrange
    # Act
    n = get_citation_count(sample_doi)
    # Assert
    assert n >= 0


def test_get_citation_count_returns_zero_for_unknown_doi():
    # Arrange
    # Act
    n = get_citation_count("10.0000/nonexistent")
    # Assert
    assert n == 0


# ---------- CitationNode ----------


def test_citation_node_constructor_stores_doi_with_minimal_args():
    # Arrange
    doi = "10.1234/test"
    # Act
    node = CitationNode(doi=doi)
    # Assert
    assert node.doi == doi


def test_citation_node_default_title_is_empty_string():
    # Arrange
    # Act
    node = CitationNode(doi="10.1234/test")
    # Assert
    assert node.title == ""


def test_citation_node_default_authors_is_empty_list():
    # Arrange
    # Act
    node = CitationNode(doi="10.1234/test")
    # Assert
    assert node.authors == []


def test_citation_node_default_year_is_none():
    # Arrange
    # Act
    node = CitationNode(doi="10.1234/test")
    # Assert
    assert node.year is None


def test_citation_node_default_journal_is_empty_string():
    # Arrange
    # Act
    node = CitationNode(doi="10.1234/test")
    # Assert
    assert node.journal == ""


def test_citation_node_default_citation_count_is_zero():
    # Arrange
    # Act
    node = CitationNode(doi="10.1234/test")
    # Assert
    assert node.citation_count == 0


def test_citation_node_default_depth_is_zero():
    # Arrange
    # Act
    node = CitationNode(doi="10.1234/test")
    # Assert
    assert node.depth == 0


@pytest.fixture
def _full_citation_node():
    return CitationNode(
        doi="10.1234/test",
        title="Test Paper",
        authors=["Author One", "Author Two"],
        year=2023,
        journal="Test Journal",
        citation_count=42,
        depth=1,
    )


def test_citation_node_full_constructor_preserves_title(_full_citation_node):
    # Arrange
    node = _full_citation_node
    # Act
    # Assert
    assert node.title == "Test Paper"


def test_citation_node_full_constructor_preserves_author_count(_full_citation_node):
    # Arrange
    node = _full_citation_node
    # Act
    # Assert
    assert len(node.authors) == 2


def test_citation_node_full_constructor_preserves_year(_full_citation_node):
    # Arrange
    node = _full_citation_node
    # Act
    # Assert
    assert node.year == 2023


def test_citation_node_full_constructor_preserves_journal(_full_citation_node):
    # Arrange
    node = _full_citation_node
    # Act
    # Assert
    assert node.journal == "Test Journal"


def test_citation_node_full_constructor_preserves_citation_count(_full_citation_node):
    # Arrange
    node = _full_citation_node
    # Act
    # Assert
    assert node.citation_count == 42


def test_citation_node_full_constructor_preserves_depth(_full_citation_node):
    # Arrange
    node = _full_citation_node
    # Act
    # Assert
    assert node.depth == 1


@pytest.fixture
def _simple_node_dict():
    node = CitationNode(doi="10.1234/test", title="Test", year=2023)
    return node.to_dict()


def test_citation_node_to_dict_returns_dict_instance(_simple_node_dict):
    # Arrange
    # Act
    # Assert
    assert isinstance(_simple_node_dict, dict)


def test_citation_node_to_dict_serialises_doi(_simple_node_dict):
    # Arrange
    # Act
    # Assert
    assert _simple_node_dict["doi"] == "10.1234/test"


def test_citation_node_to_dict_serialises_title(_simple_node_dict):
    # Arrange
    # Act
    # Assert
    assert _simple_node_dict["title"] == "Test"


def test_citation_node_to_dict_serialises_year(_simple_node_dict):
    # Arrange
    # Act
    # Assert
    assert _simple_node_dict["year"] == 2023


# ---------- CitationEdge ----------


def test_citation_edge_constructor_stores_citing_doi():
    # Arrange
    # Act
    edge = CitationEdge(citing_doi="10.1234/citing", cited_doi="10.1234/cited")
    # Assert
    assert edge.citing_doi == "10.1234/citing"


def test_citation_edge_constructor_stores_cited_doi():
    # Arrange
    # Act
    edge = CitationEdge(citing_doi="10.1234/citing", cited_doi="10.1234/cited")
    # Assert
    assert edge.cited_doi == "10.1234/cited"


def test_citation_edge_constructor_stores_optional_year():
    # Arrange
    # Act
    edge = CitationEdge(
        citing_doi="10.1234/citing",
        cited_doi="10.1234/cited",
        year=2023,
    )
    # Assert
    assert edge.year == 2023


# ---------- CitationNetwork ----------


@pytest.fixture
def _depth_one_network(sample_doi):
    return CitationNetwork(sample_doi, depth=1, max_citing=3, max_cited=3)


def test_citation_network_constructor_stores_center_doi(sample_doi):
    # Arrange
    # Act
    network = CitationNetwork(sample_doi, depth=1, max_citing=5, max_cited=5)
    # Assert
    assert network.center_doi == sample_doi


def test_citation_network_constructor_stores_depth(sample_doi):
    # Arrange
    # Act
    network = CitationNetwork(sample_doi, depth=1, max_citing=5, max_cited=5)
    # Assert
    assert network.depth == 1


def test_citation_network_nodes_attribute_is_dict_instance(_depth_one_network):
    # Arrange
    # Act
    nodes = _depth_one_network.nodes
    # Assert
    assert isinstance(nodes, dict)


def test_citation_network_edges_attribute_is_list_instance(_depth_one_network):
    # Arrange
    # Act
    edges = _depth_one_network.edges
    # Assert
    assert isinstance(edges, list)


def test_citation_network_nodes_dict_contains_center_doi_key(
    _depth_one_network, sample_doi
):
    # Arrange
    # Act
    # Assert
    assert sample_doi in _depth_one_network.nodes


@pytest.fixture
def _depth_one_network_dict(_depth_one_network):
    return _depth_one_network.to_dict()


def test_citation_network_to_dict_returns_dict_instance(_depth_one_network_dict):
    # Arrange
    # Act
    # Assert
    assert isinstance(_depth_one_network_dict, dict)


def test_citation_network_to_dict_serialises_center_doi(
    _depth_one_network_dict, sample_doi
):
    # Arrange
    # Act
    # Assert
    assert _depth_one_network_dict["center_doi"] == sample_doi


def test_citation_network_to_dict_contains_nodes_field(_depth_one_network_dict):
    # Arrange
    # Act
    # Assert
    assert "nodes" in _depth_one_network_dict


def test_citation_network_to_dict_contains_edges_field(_depth_one_network_dict):
    # Arrange
    # Act
    # Assert
    assert "edges" in _depth_one_network_dict


def test_citation_network_to_dict_contains_stats_field(_depth_one_network_dict):
    # Arrange
    # Act
    # Assert
    assert "stats" in _depth_one_network_dict


def test_citation_network_repr_mentions_class_name(_depth_one_network):
    # Arrange
    # Act
    rendered = repr(_depth_one_network)
    # Assert
    assert "CitationNetwork" in rendered


def test_citation_network_repr_includes_center_doi(_depth_one_network, sample_doi):
    # Arrange
    # Act
    rendered = repr(_depth_one_network)
    # Assert
    assert sample_doi in rendered


def test_citation_network_depth_zero_still_contains_center_doi(sample_doi):
    # Arrange
    # Act
    network = CitationNetwork(sample_doi, depth=0)
    # Assert
    assert sample_doi in network.nodes


# ---------- CitationNetwork visualization (best-effort) ----------


def test_citation_network_to_networkx_returns_digraph_when_networkx_available(
    sample_doi,
):
    # Arrange
    network = CitationNetwork(sample_doi, depth=0)
    try:
        import networkx as nx
    except ImportError:
        pytest.skip("networkx not installed")
    # Act
    graph = network.to_networkx()
    # Assert
    assert isinstance(graph, nx.DiGraph)


def test_citation_network_save_html_writes_output_when_pyvis_available(
    sample_doi, tmp_path
):
    # Arrange
    pytest.importorskip("pyvis")
    pytest.importorskip("networkx")
    network = CitationNetwork(sample_doi, depth=0)
    output = tmp_path / "test_network.html"
    # Act
    network.save_html(str(output))
    # Assert
    assert output.exists()


def test_citation_network_save_png_writes_output_when_matplotlib_available(
    sample_doi, tmp_path
):
    # Arrange
    pytest.importorskip("matplotlib")
    pytest.importorskip("networkx")
    network = CitationNetwork(sample_doi, depth=0)
    output = tmp_path / "test_network.png"
    # Act
    network.save_png(str(output))
    # Assert
    assert output.exists()


# ---------- CitationNetwork stats ----------


def test_citation_network_stats_total_nodes_matches_nodes_dict_length(
    _depth_one_network,
):
    # Arrange
    network = _depth_one_network
    # Act
    stats = network.to_dict()["stats"]
    # Assert
    assert stats["total_nodes"] == len(network.nodes)


def test_citation_network_stats_total_edges_matches_edges_list_length(
    _depth_one_network,
):
    # Arrange
    network = _depth_one_network
    # Act
    stats = network.to_dict()["stats"]
    # Assert
    assert stats["total_edges"] == len(network.edges)
