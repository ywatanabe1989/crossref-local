# Impact Factor Calculation System

## Overview

This system calculates Journal Impact Factors (IF) from the local CrossRef database,
following the Clarivate/JCR methodology.

---

## The Clarivate Impact Factor Formula

### 2-Year Impact Factor (Standard)

```
IF(2023) = Citations in 2023 to articles published in 2021-2022
           ─────────────────────────────────────────────────────
           Citable items published in 2021-2022
```

### 5-Year Impact Factor

```
IF_5yr(2023) = Citations in 2023 to articles published in 2018-2022
               ─────────────────────────────────────────────────────
               Citable items published in 2018-2022
```

### Key Definition: "Citable Items"

JCR only counts **citable items** in both numerator and denominator:
- ✅ Research articles
- ✅ Review articles
- ❌ News items
- ❌ Editorials
- ❌ Letters to editor
- ❌ Corrections
- ❌ Book reviews

**Our proxy**: Articles with >20 references are considered citable items.
This effectively filters out news, editorials, and short communications.

---

## Database Schema

### Tables Used

```
works (112M rows)
├── doi: Article DOI
├── metadata: JSON blob with full CrossRef metadata
├── type: "journal-article", "book-chapter", etc.
└── Indexes:
    ├── idx_issn: json_extract(metadata, '$.ISSN[0]')
    ├── idx_issn_year: (ISSN, publication_year) - COMPOUND INDEX
    └── idx_published_year: publication year

citations (500M+ rows)
├── citing_doi: DOI of the citing article
├── cited_doi: DOI being cited
├── citing_year: Year of the citing article
└── Indexes:
    └── idx_citations_cited_new: (cited_doi, citing_year)

journals_openalex (222K journals)
├── issn_l: Linking ISSN
├── name: Journal name
├── 2yr_mean_citedness: OpenAlex IF proxy
└── h_index: Journal h-index
```

---

## Speed Optimization

### Performance Timeline

| Version | 2-Year IF Time | Speedup |
|---------|---------------|---------|
| Initial (no index) | ~2 minutes | 1x |
| + idx_issn_year | 1.7 seconds | 70x |
| + citable_only filter | **0.4 seconds** | **300x** |

### Key Optimizations

1. **Compound Index** (`idx_issn_year`)
   - Indexes both ISSN and year together
   - Eliminates full table scans for journal+year queries
   - Build time: ~7 hours for 112M rows

2. **Citations Table Index** (`idx_citations_cited_new`)
   - Pre-indexed (cited_doi, citing_year)
   - Instant lookup for year-specific citations

3. **DOI-Only Queries**
   - Only fetch DOIs, not full metadata
   - Reduces data transfer significantly

4. **Citable Items Filter**
   - Fewer articles = faster citation counting
   - ~70% reduction in articles to process

---

## Correlation with Official JCR

### OpenAlex vs JCR Comparison (20,554 journals)

```
Pearson r:  0.67 (p < 0.001)
Spearman r: 0.85 (p < 0.001) ← Strong rank correlation!
```

OpenAlex `2yr_mean_citedness` is systematically lower than JCR IF,
but the ranking is highly correlated.

### Our Calculation vs JCR (2023)

**Journals with Good Citation Coverage (~100%):**

| Journal | ISSN | Citable Items | Calc IF | JCR IF | Match |
|---------|------|---------------|---------|--------|-------|
| Nature | 0028-0836 | 2,133 | 54.07 | ~50 | ✅ |
| Science | 0036-8075 | 1,545 | 46.17 | ~45 | ✅ |
| Cell | 0092-8674 | 657 | 54.01 | ~60 | ✅ |
| PNAS | 0027-8424 | 6,873 | 10.22 | ~10 | ✅ |
| Nature Medicine | 1078-8956 | 476 | 56.13 | ~58 | ✅ |
| Nature Communications | 2041-1723 | 14,357 | 16.14 | ~16 | ✅ |
| Neuron | 0896-6273 | 485 | 19.09 | ~17 | ✅ |
| Nat Biomed Eng | 2157-846X | 231 | 30.51 | ~28 | ✅ |
| Biomaterials | 0142-9612 | 1,234 | 13.54 | ~14 | ✅ |
| NeuroImage | 1053-8119 | 1,914 | 6.35 | ~5 | ✅ |
| J Neural Eng | 1741-2560 | 732 | 4.55 | ~5 | ✅ |

**Journals with Poor Citation Coverage (<10%) - USE WITH CAUTION:**

| Journal | ISSN | Coverage | Calc IF | JCR IF | Issue |
|---------|------|----------|---------|--------|-------|
| The Lancet | 0140-6736 | 4.5% | 3.70 | ~98 | ❌ Incomplete citations |
| NEJM | 0028-4793 | 9.3% | 2.61 | ~150 | ❌ Incomplete citations |
| J Neurosci | 0270-6474 | 1.7% | 0.15 | ~5 | ❌ Incomplete citations |

---

## Usage

### Basic Usage

```python
from impact_factor.src.calculator import ImpactFactorCalculator

with ImpactFactorCalculator(db_path) as calc:
    result = calc.calculate_impact_factor(
        journal_identifier="Nature",
        target_year=2023,
        window_years=2,        # 2-year IF (default)
        citable_only=True      # JCR methodology (default)
    )
    print(f"IF: {result['impact_factor']:.2f}")
```

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `journal_identifier` | required | Journal name or ISSN |
| `target_year` | required | Year for IF calculation |
| `window_years` | 2 | Citation window (2 or 5) |
| `use_issn` | False | If True, identifier is ISSN |
| `method` | "citations-table" | Citation counting method |
| `citable_only` | True | Only count citable items |

### Methods for Citation Counting

| Method | Speed | Accuracy | Description |
|--------|-------|----------|-------------|
| `citations-table` | Fast | Year-specific | Uses pre-built citations table |
| `is-referenced-by` | Fast | Cumulative only | Uses CrossRef metadata field |
| `reference-graph` | Slow | Most accurate | Builds citation graph from references |

---

## Command Line

```bash
# 2-year IF for Nature in 2023
python examples/demo.py --journal Nature --year 2023

# 5-year IF
python examples/demo.py --journal Nature --year 2023 --duration 5

# Different journal
python examples/demo.py --journal "The Lancet" --year 2023
```

---

## Limitations

1. **Citation Coverage**: Our citations table may be incomplete for some journals
   - Nature, Science, Cell: ~100% coverage ✅
   - The Lancet, NEJM: ~5-10% coverage ❌ (underestimates IF)
   - Medical/clinical journals tend to have lower coverage

2. **Citable Items**: >20 references is a heuristic, not perfect

3. **Article Types**: CrossRef doesn't always distinguish article types

4. **Self-Citations**: Currently included (JCR reports both with/without)

### Citation Coverage Check

For journals with low coverage, use `is-referenced-by` method instead:

```python
# For journals with poor coverage (medical/clinical)
result = calc.calculate_impact_factor(
    journal_identifier="0140-6736",  # Lancet
    target_year=2023,
    method="is-referenced-by",  # Use cumulative citations
    citable_only=True
)
```

Note: `is-referenced-by` gives cumulative citations (not year-specific),
so this is an approximation.

---

## References

- Clarivate Impact Factor Essay: https://clarivate.com/academia-government/essays/impact-factor/
- OpenAlex API: https://docs.openalex.org/api-entities/sources
- CrossRef API: https://api.crossref.org/

