HTTP API Reference
==================

CrossRef Local provides a RESTful HTTP API via the relay server.

Starting the Server
-------------------

.. code-block:: bash

    crossref-local relay --port 31291

The API documentation is available at ``http://localhost:31291/docs``.

Endpoints
---------

Root
~~~~

.. code-block:: http

    GET /

Returns API information and available endpoints.

Health Check
~~~~~~~~~~~~

.. code-block:: http

    GET /health

Returns server health status.

Database Info
~~~~~~~~~~~~~

.. code-block:: http

    GET /info

Returns database statistics (total works, FTS indexed count).

Search Works
~~~~~~~~~~~~

.. code-block:: http

    GET /works?q=<query>&limit=<n>&offset=<n>

Parameters:

- ``q`` (required): Search query (FTS5 syntax supported)
- ``limit`` (optional): Max results (default: 10, max: 100)
- ``offset`` (optional): Skip first N results

Example:

.. code-block:: bash

    curl "http://localhost:31291/works?q=machine%20learning&limit=10"

Response:

.. code-block:: json

    {
      "query": "machine learning",
      "total": 1234567,
      "returned": 10,
      "elapsed_ms": 45.2,
      "results": [
        {
          "doi": "10.1234/example",
          "title": "Machine Learning Methods",
          "authors": ["Author One", "Author Two"],
          "year": 2023,
          "journal": "Nature",
          "abstract": "..."
        }
      ]
    }

Get Work by DOI
~~~~~~~~~~~~~~~

.. code-block:: http

    GET /works/{doi}

Example:

.. code-block:: bash

    curl "http://localhost:31291/works/10.1038/nature12373"

Batch Lookup
~~~~~~~~~~~~

.. code-block:: http

    POST /works/batch

Request body:

.. code-block:: json

    {
      "dois": ["10.1038/nature12373", "10.1126/science.aax0758"]
    }

Citations
---------

Get Citing Papers
~~~~~~~~~~~~~~~~~

.. code-block:: http

    GET /citations/{doi}/citing?limit=<n>

Returns DOIs of papers that cite the given work.

Get Cited Papers
~~~~~~~~~~~~~~~~

.. code-block:: http

    GET /citations/{doi}/cited?limit=<n>

Returns DOIs of papers that the given work cites (references).

Citation Count
~~~~~~~~~~~~~~

.. code-block:: http

    GET /citations/{doi}/count

Returns the number of citations for a work.

Citation Network
~~~~~~~~~~~~~~~~

.. code-block:: http

    GET /citations/{doi}/network?depth=<n>&max_citing=<n>&max_cited=<n>

Returns a citation network graph.

FTS5 Query Syntax
-----------------

The search supports FTS5 query syntax:

- Simple terms: ``machine learning``
- Exact phrases: ``"neural network"``
- Boolean operators: ``CRISPR AND gene editing``
- Exclusion: ``machine learning NOT deep``
- Prefix matching: ``neuro*``

Examples:

.. code-block:: bash

    # Simple search
    curl "http://localhost:31291/works?q=CRISPR"

    # Phrase search
    curl "http://localhost:31291/works?q=\"deep%20learning\""

    # Boolean
    curl "http://localhost:31291/works?q=machine%20AND%20learning%20NOT%20deep"
