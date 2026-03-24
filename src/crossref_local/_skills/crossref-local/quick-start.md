# Quick Start

```python
from crossref_local import search, get, count

# Full-text search (22ms for 541 matches across 167M records)
results = search("hippocampal sharp wave ripples")
for work in results:
    print(f"{work.title} ({work.year})")

# Get by DOI
work = get("10.1126/science.aax0758")
print(work.citation())

# Count matches
n = count("machine learning")  # 477,922 matches
```

## Output Formats

Every search returns `Work` objects with consistent attributes:

```python
work = get("10.1038/nature12373")
# Attributes: doi, title, year, authors, journal, abstract,
#             citation_count, references, type, member
work.citation()  # Formatted citation string
```
