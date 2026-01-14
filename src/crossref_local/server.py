"""FastAPI server for CrossRef Local with FTS5 search.

This server provides proper full-text search using FTS5 index,
unlike the Django API which only scans a limited subset.

Usage:
    crossref-local api                    # Run on default port 8333
    crossref-local api --port 8080        # Custom port

    # Or directly:
    uvicorn crossref_local.server:app --host 0.0.0.0 --port 8333
"""

import time
from typing import Optional, List

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from . import fts, __version__
from .db import get_db
from .models import Work

app = FastAPI(
    title="CrossRef Local API",
    description="Fast full-text search across 167M+ scholarly works",
    version=__version__,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class WorkResponse(BaseModel):
    doi: str
    title: Optional[str] = None
    authors: List[str] = []
    year: Optional[int] = None
    journal: Optional[str] = None
    issn: Optional[str] = None
    volume: Optional[str] = None
    issue: Optional[str] = None
    page: Optional[str] = None
    abstract: Optional[str] = None
    citation_count: Optional[int] = None


class SearchResponse(BaseModel):
    query: str
    total: int
    returned: int
    elapsed_ms: float
    results: List[WorkResponse]


class InfoResponse(BaseModel):
    name: str = "CrossRef Local API"
    version: str = __version__
    status: str = "running"
    mode: str = "local"
    total_papers: int
    fts_indexed: int
    citations: int
    database_path: str


@app.get("/")
def root():
    """API root with endpoint information."""
    return {
        "name": "CrossRef Local API",
        "version": __version__,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "info": "/info",
            "search": "/works?q=<query>",
            "get_by_doi": "/works/{doi}",
            "batch": "/works/batch",
        },
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    db = get_db()
    return {
        "status": "healthy",
        "database_connected": db is not None,
        "database_path": str(db.db_path) if db else None,
    }


@app.get("/info", response_model=InfoResponse)
def info():
    """Get database statistics."""
    db = get_db()

    row = db.fetchone("SELECT COUNT(*) as count FROM works")
    work_count = row["count"] if row else 0

    try:
        row = db.fetchone("SELECT COUNT(*) as count FROM works_fts")
        fts_count = row["count"] if row else 0
    except Exception:
        fts_count = 0

    try:
        row = db.fetchone("SELECT COUNT(*) as count FROM citations")
        citation_count = row["count"] if row else 0
    except Exception:
        citation_count = 0

    return InfoResponse(
        total_papers=work_count,
        fts_indexed=fts_count,
        citations=citation_count,
        database_path=str(db.db_path),
    )


@app.get("/works", response_model=SearchResponse)
def search_works(
    q: str = Query(..., description="Search query (FTS5 syntax supported)"),
    limit: int = Query(10, ge=1, le=100, description="Max results"),
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


@app.get("/works/{doi:path}", response_model=Optional[WorkResponse])
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


class BatchRequest(BaseModel):
    dois: List[str]


class BatchResponse(BaseModel):
    requested: int
    found: int
    results: List[WorkResponse]


@app.post("/works/batch", response_model=BatchResponse)
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


# For backwards compatibility with existing API endpoints
@app.get("/api/search/")
def api_search_compat(
    title: Optional[str] = None,
    q: Optional[str] = None,
    doi: Optional[str] = None,
    limit: int = 10,
):
    """Backwards-compatible search endpoint."""
    query = title or q

    if doi:
        # DOI lookup
        try:
            work = get_work(doi)
            return {
                "query": {"doi": doi},
                "results": [work.model_dump()],
                "total": 1,
                "returned": 1,
            }
        except HTTPException:
            return {"query": {"doi": doi}, "results": [], "total": 0, "returned": 0}

    if not query:
        raise HTTPException(
            status_code=400, detail="Specify q, title, or doi parameter"
        )

    # Call fts.search directly (not the endpoint function)
    results = fts.search(query, limit=limit, offset=0)
    return {
        "query": {
            "title": query,
            "doi": None,
            "year": None,
            "authors": None,
            "limit": limit,
        },
        "results": [
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
            ).model_dump()
            for w in results.works
        ],
        "total": results.total,
        "returned": len(results.works),
    }


@app.get("/api/stats/")
def api_stats_compat():
    """Backwards-compatible stats endpoint."""
    db = get_db()

    row = db.fetchone("SELECT COUNT(*) as count FROM works")
    work_count = row["count"] if row else 0

    # Get table names
    tables = []
    for row in db.fetchall("SELECT name FROM sqlite_master WHERE type='table'"):
        tables.append(row["name"])

    # Get index names
    indices = []
    for row in db.fetchall("SELECT name FROM sqlite_master WHERE type='index'"):
        if row["name"]:
            indices.append(row["name"])

    return {
        "total_papers": work_count,
        "database_size_mb": None,
        "year_range": None,
        "total_journals": 0,
        "total_citations": None,
        "tables": tables,
        "indices": indices,
    }


def run_server(host: str = "0.0.0.0", port: int = 8333):
    """Run the FastAPI server."""
    import uvicorn

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
