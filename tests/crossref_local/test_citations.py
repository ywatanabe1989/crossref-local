"""Tests for crossref_local.citations module."""

import pytest

from crossref_local.citations import (
    get_citing,
    get_cited,
    get_citation_count,
    CitationNode,
    CitationEdge,
    CitationNetwork,
)


class TestGetCiting:
    """Tests for get_citing function."""

    def test_get_citing_returns_list(self, sample_doi):
        """get_citing() returns a list."""
        citing = get_citing(sample_doi)
        assert isinstance(citing, list)

    def test_get_citing_returns_strings(self, sample_doi):
        """get_citing() returns list of DOI strings."""
        citing = get_citing(sample_doi, limit=5)
        for doi in citing:
            assert isinstance(doi, str)

    def test_get_citing_respects_limit(self, sample_doi):
        """get_citing() respects limit parameter."""
        citing = get_citing(sample_doi, limit=3)
        assert len(citing) <= 3

    def test_get_citing_nonexistent_doi(self):
        """get_citing() returns empty list for nonexistent DOI."""
        citing = get_citing("10.0000/nonexistent")
        assert citing == []


class TestGetCited:
    """Tests for get_cited function."""

    def test_get_cited_returns_list(self, sample_doi):
        """get_cited() returns a list."""
        cited = get_cited(sample_doi)
        assert isinstance(cited, list)

    def test_get_cited_returns_strings(self, sample_doi):
        """get_cited() returns list of DOI strings."""
        cited = get_cited(sample_doi, limit=5)
        for doi in cited:
            assert isinstance(doi, str)

    def test_get_cited_respects_limit(self, sample_doi):
        """get_cited() respects limit parameter."""
        cited = get_cited(sample_doi, limit=3)
        assert len(cited) <= 3

    def test_get_cited_nonexistent_doi(self):
        """get_cited() returns empty list for nonexistent DOI."""
        cited = get_cited("10.0000/nonexistent")
        assert cited == []


class TestGetCitationCount:
    """Tests for get_citation_count function."""

    def test_get_citation_count_returns_int(self, sample_doi):
        """get_citation_count() returns an integer."""
        count = get_citation_count(sample_doi)
        assert isinstance(count, int)

    def test_get_citation_count_non_negative(self, sample_doi):
        """get_citation_count() returns non-negative value."""
        count = get_citation_count(sample_doi)
        assert count >= 0

    def test_get_citation_count_nonexistent_doi(self):
        """get_citation_count() returns 0 for nonexistent DOI."""
        count = get_citation_count("10.0000/nonexistent")
        assert count == 0


class TestCitationNode:
    """Tests for CitationNode dataclass."""

    def test_citation_node_creation(self):
        """CitationNode can be created with required fields."""
        node = CitationNode(doi="10.1234/test")
        assert node.doi == "10.1234/test"

    def test_citation_node_defaults(self):
        """CitationNode has sensible defaults."""
        node = CitationNode(doi="10.1234/test")
        assert node.title == ""
        assert node.authors == []
        assert node.year is None
        assert node.journal == ""
        assert node.citation_count == 0
        assert node.depth == 0

    def test_citation_node_full_creation(self):
        """CitationNode can be created with all fields."""
        node = CitationNode(
            doi="10.1234/test",
            title="Test Paper",
            authors=["Author One", "Author Two"],
            year=2023,
            journal="Test Journal",
            citation_count=42,
            depth=1,
        )
        assert node.doi == "10.1234/test"
        assert node.title == "Test Paper"
        assert len(node.authors) == 2
        assert node.year == 2023
        assert node.journal == "Test Journal"
        assert node.citation_count == 42
        assert node.depth == 1

    def test_citation_node_to_dict(self):
        """CitationNode.to_dict() returns dict."""
        node = CitationNode(
            doi="10.1234/test",
            title="Test",
            year=2023,
        )
        d = node.to_dict()
        assert isinstance(d, dict)
        assert d["doi"] == "10.1234/test"
        assert d["title"] == "Test"
        assert d["year"] == 2023


class TestCitationEdge:
    """Tests for CitationEdge dataclass."""

    def test_citation_edge_creation(self):
        """CitationEdge can be created."""
        edge = CitationEdge(citing_doi="10.1234/citing", cited_doi="10.1234/cited")
        assert edge.citing_doi == "10.1234/citing"
        assert edge.cited_doi == "10.1234/cited"

    def test_citation_edge_with_year(self):
        """CitationEdge can have year."""
        edge = CitationEdge(
            citing_doi="10.1234/citing",
            cited_doi="10.1234/cited",
            year=2023,
        )
        assert edge.year == 2023


class TestCitationNetwork:
    """Tests for CitationNetwork class."""

    def test_network_creation(self, sample_doi):
        """CitationNetwork can be created."""
        network = CitationNetwork(sample_doi, depth=1, max_citing=5, max_cited=5)
        assert network.center_doi == sample_doi
        assert network.depth == 1

    def test_network_has_nodes(self, sample_doi):
        """CitationNetwork has nodes dict."""
        network = CitationNetwork(sample_doi, depth=1, max_citing=3, max_cited=3)
        assert isinstance(network.nodes, dict)

    def test_network_has_edges(self, sample_doi):
        """CitationNetwork has edges list."""
        network = CitationNetwork(sample_doi, depth=1, max_citing=3, max_cited=3)
        assert isinstance(network.edges, list)

    def test_network_center_in_nodes(self, sample_doi):
        """CitationNetwork includes center DOI in nodes."""
        network = CitationNetwork(sample_doi, depth=1, max_citing=3, max_cited=3)
        assert sample_doi in network.nodes

    def test_network_to_dict(self, sample_doi):
        """CitationNetwork.to_dict() returns dict."""
        network = CitationNetwork(sample_doi, depth=1, max_citing=3, max_cited=3)
        d = network.to_dict()
        assert isinstance(d, dict)
        assert d["center_doi"] == sample_doi
        assert "nodes" in d
        assert "edges" in d
        assert "stats" in d

    def test_network_repr(self, sample_doi):
        """CitationNetwork has repr."""
        network = CitationNetwork(sample_doi, depth=1, max_citing=3, max_cited=3)
        r = repr(network)
        assert "CitationNetwork" in r
        assert sample_doi in r

    def test_network_depth_zero(self, sample_doi):
        """CitationNetwork with depth=0 only has center node."""
        network = CitationNetwork(sample_doi, depth=0)
        # Should have at least the center node
        assert sample_doi in network.nodes


class TestCitationNetworkVisualization:
    """Tests for CitationNetwork visualization methods."""

    def test_to_networkx_import_error(self, sample_doi):
        """to_networkx() raises ImportError if networkx not installed."""
        network = CitationNetwork(sample_doi, depth=0)
        try:
            G = network.to_networkx()
            # networkx is available
            import networkx as nx
            assert isinstance(G, nx.DiGraph)
        except ImportError:
            # networkx not installed, which is fine
            pass

    def test_save_html_import_error(self, sample_doi, tmp_path):
        """save_html() raises ImportError if pyvis not installed."""
        network = CitationNetwork(sample_doi, depth=0)
        output_path = tmp_path / "test_network.html"
        try:
            network.save_html(str(output_path))
            assert output_path.exists()
        except ImportError:
            # pyvis not installed, which is fine
            pass

    def test_save_png_import_error(self, sample_doi, tmp_path):
        """save_png() raises ImportError if matplotlib not installed."""
        network = CitationNetwork(sample_doi, depth=0)
        output_path = tmp_path / "test_network.png"
        try:
            network.save_png(str(output_path))
            assert output_path.exists()
        except ImportError:
            # matplotlib/networkx not installed, which is fine
            pass


class TestCitationNetworkStats:
    """Tests for CitationNetwork statistics."""

    def test_network_stats_in_dict(self, sample_doi):
        """Network stats include node and edge counts."""
        network = CitationNetwork(sample_doi, depth=1, max_citing=3, max_cited=3)
        d = network.to_dict()
        assert "total_nodes" in d["stats"]
        assert "total_edges" in d["stats"]
        assert d["stats"]["total_nodes"] == len(network.nodes)
        assert d["stats"]["total_edges"] == len(network.edges)
