"""Work search and retrieval endpoints."""

import time
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from .._core import fts
from .._core.db import get_db
from .._core.models import Work
from .models import WorkResponse, SearchResponse, BatchRequest, BatchResponse

router = APIRouter(tags=["works"])


@router.get("/works", response_model=SearchResponse)
def search_works(
    q: str = Query(..., description="Search query (FTS5 syntax supported)"),
    limit: int = Query(10, ge=1, description="Max results"),
    offset: int = Query(0, ge=0, description="Skip first N results"),
):
    """
    Full-text search across works.

    Uses FTS5 index for fast searching across titles, abstracts, and authors.
    Supports FTS5 query syntax like AND, OR, NOT, "exact phrases".

    Examples:
        /works?q=machine learning
        /works?q="neural network" AND hippocampus
        /works?q=CRISPR&limit=20
    """
    start = time.perf_counter()

    try:
        results = fts.search(q, limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Search error: {e}")

    elapsed_ms = (time.perf_counter() - start) * 1000

    return SearchResponse(
        query=q,
        total=results.total,
        returned=len(results.works),
        elapsed_ms=round(elapsed_ms, 2),
        results=[
            WorkResponse(
                doi=w.doi,
                title=w.title,
                authors=w.authors,
                year=w.year,
                journal=w.journal,
                issn=w.issn,
                volume=w.volume,
                issue=w.issue,
                page=w.page,
                abstract=w.abstract,
                citation_count=w.citation_count,
            )
            for w in results.works
        ],
    )


@router.get("/works/{doi:path}", response_model=Optional[WorkResponse])
def get_work(doi: str):
    """
    Get work metadata by DOI.

    Examples:
        /works/10.1038/nature12373
        /works/10.1016/j.cell.2020.01.001
    """
    db = get_db()
    metadata = db.get_metadata(doi)

    if metadata is None:
        raise HTTPException(status_code=404, detail=f"DOI not found: {doi}")

    work = Work.from_metadata(doi, metadata)

    return WorkResponse(
        doi=work.doi,
        title=work.title,
        authors=work.authors,
        year=work.year,
        journal=work.journal,
        issn=work.issn,
        volume=work.volume,
        issue=work.issue,
        page=work.page,
        abstract=work.abstract,
        citation_count=work.citation_count,
    )


@router.post("/works/batch", response_model=BatchResponse)
def get_works_batch(request: BatchRequest):
    """
    Get multiple works by DOI.

    Request body: {"dois": ["10.1038/...", "10.1016/..."]}
    """
    db = get_db()
    results = []

    for doi in request.dois:
        metadata = db.get_metadata(doi)
        if metadata:
            work = Work.from_metadata(doi, metadata)
            results.append(
                WorkResponse(
                    doi=work.doi,
                    title=work.title,
                    authors=work.authors,
                    year=work.year,
                    journal=work.journal,
                    abstract=work.abstract,
                    citation_count=work.citation_count,
                )
            )

    return BatchResponse(
        requested=len(request.dois),
        found=len(results),
        results=results,
    )
