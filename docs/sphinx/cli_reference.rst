CLI Reference
=============

CrossRef Local provides a comprehensive command-line interface.

Global Options
--------------

.. code-block:: bash

    crossref-local [OPTIONS] COMMAND [ARGS]...

Options:

- ``--http``: Use HTTP API instead of direct database
- ``--api-url URL``: API URL for http mode (default: auto-detect)
- ``--version``: Show version
- ``-h, --help``: Show help
- ``--help-recursive``: Show help for all commands

Commands
--------

search
~~~~~~

Search for works by title, abstract, or authors.

.. code-block:: bash

    crossref-local search [OPTIONS] QUERY

Options:

- ``-n, --number INTEGER``: Number of results (default: 10)
- ``-o, --offset INTEGER``: Skip first N results
- ``-a, --abstracts``: Show abstracts
- ``-A, --authors``: Show authors
- ``-if, --impact-factor``: Show journal impact factor
- ``--json``: Output as JSON

Examples:

.. code-block:: bash

    crossref-local search "machine learning"
    crossref-local search "CRISPR" -n 20 -a
    crossref-local search "neural networks" --impact-factor
    crossref-local search "deep learning" --json

search-by-doi
~~~~~~~~~~~~~

Search for a work by DOI.

.. code-block:: bash

    crossref-local search-by-doi DOI [OPTIONS]

Options:

- ``--json``: Output as JSON
- ``--citation``: Output as citation

Examples:

.. code-block:: bash

    crossref-local search-by-doi 10.1038/nature12373
    crossref-local search-by-doi 10.1038/nature12373 --citation

status
~~~~~~

Show status and configuration.

.. code-block:: bash

    crossref-local status

relay
~~~~~

Run HTTP relay server for remote database access.

.. code-block:: bash

    crossref-local relay [OPTIONS]

Options:

- ``--host TEXT``: Host to bind (default: 0.0.0.0)
- ``--port INTEGER``: Port to listen on (default: 31291)

Examples:

.. code-block:: bash

    crossref-local relay
    crossref-local relay --port 8080

MCP Commands
------------

mcp start
~~~~~~~~~

Start the MCP server.

.. code-block:: bash

    crossref-local mcp start [OPTIONS]

Options:

- ``-t, --transport [stdio|sse|http]``: Transport type (default: stdio)
- ``--host TEXT``: Host for SSE/HTTP transport
- ``--port INTEGER``: Port for SSE/HTTP transport

mcp tools
~~~~~~~~~

List available MCP tools.

.. code-block:: bash

    crossref-local mcp tools

list-apis
~~~~~~~~~

List Python APIs (requires scitex).

.. code-block:: bash

    crossref-local list-apis [OPTIONS]

Options:

- ``-v, --verbose``: Verbosity level (-v sig, -vv +doc, -vvv full)
- ``-d, --max-depth INTEGER``: Max recursion depth
- ``--json``: Output as JSON
