# Common Workflows

## "I need to find papers on a topic"

```python
from crossref_local import search

results = search("CRISPR genome editing", limit=20)
for work in results:
    print(f"{work.title} ({work.year}) - {work.doi}")
```

## "I have DOIs and need metadata"

```python
from crossref_local import get, get_many, enrich_dois

# Single DOI
work = get("10.1038/nature12373")

# Multiple DOIs
works = get_many(["10.1038/nature12373", "10.1126/science.aax0758"])

# Enrich with citation counts and references
enriched = enrich_dois(["10.1038/nature12373"])
```

## "I need citation information"

```python
from crossref_local import get_citing, get_cited, get_citation_count

citing = get_citing("10.1038/nature12373")   # Papers citing this work
cited = get_cited("10.1038/nature12373")     # Papers this work cites
count = get_citation_count("10.1038/nature12373")  # 1539
```

## "I want to validate my bibliography"

```python
from crossref_local import check_bibtex, check_citations

# Check a BibTeX file
report = check_bibtex("references.bib")

# Check DOIs in a list
report = check_doi_list("dois.txt")
```

## "I need a citation network visualization"

```python
from crossref_local import CitationNetwork

network = CitationNetwork("10.1038/nature12373", depth=2)
network.save_html("citation_network.html")  # requires: pip install crossref-local[viz]
```

## "I want to calculate impact factors"

```python
from crossref_local.impact_factor import ImpactFactorCalculator

with ImpactFactorCalculator() as calc:
    result = calc.calculate_impact_factor("Nature", target_year=2023)
    print(f"IF: {result['impact_factor']:.3f}")  # 54.067
```

## "I need async operations"

```python
from crossref_local import aio

async def main():
    counts = await aio.count_many(["CRISPR", "neural network", "climate"])
    results = await aio.search("machine learning")
```
