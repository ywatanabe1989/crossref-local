---
package: crossref-local
skill: async
---

# Async API

The `crossref_local.aio` module provides async versions of all core API
functions using thread pool execution with per-thread database connections.

## Import

```python
from crossref_local import aio
# or individual functions
from crossref_local.aio import search, get, count, count_many
```

## Available Functions

| Function | Async signature |
|----------|----------------|
| `aio.search` | `async (query, limit=10, offset=0, with_if=False) -> SearchResult` |
| `aio.count` | `async (query) -> int` |
| `aio.get` | `async (doi) -> Work | None` |
| `aio.get_many` | `async (dois: list[str]) -> list[Work]` |
| `aio.exists` | `async (doi) -> bool` |
| `aio.info` | `async () -> dict` |
| `aio.search_many` | `async (queries: list[str], ...) -> list[SearchResult]` |
| `aio.count_many` | `async (queries: list[str]) -> list[int]` |

## Examples

```python
import asyncio
from crossref_local import aio

async def main():
    # Single operations
    results = await aio.search("hippocampal sharp wave ripples")
    work = await aio.get("10.1038/nature12373")
    n = await aio.count("CRISPR AND cancer")

    # Concurrent counts
    terms = ["CRISPR", "neural network", "epilepsy", "Alzheimer"]
    counts = await aio.count_many(terms)
    for term, count in zip(terms, counts):
        print(f"{term}: {count:,} papers")

    # Concurrent searches
    queries = ["seizure prediction", "brain-computer interface"]
    results_list = await aio.search_many(queries, limit=5)

asyncio.run(main())
```

## `count_many` — Concurrent Counting

Efficient for comparing term frequencies across many queries:

```python
async def compare_topics():
    topics = [
        "deep learning AND medical imaging",
        "machine learning AND genomics",
        "natural language processing AND clinical",
    ]
    counts = await aio.count_many(topics)
    for topic, n in sorted(zip(topics, counts), key=lambda x: -x[1]):
        print(f"{n:>10,}  {topic}")
```

## Thread Safety

- Each async call runs in a thread pool worker
- Each worker gets its own database connection (per-thread singletons)
- Safe for concurrent use without connection pool management
