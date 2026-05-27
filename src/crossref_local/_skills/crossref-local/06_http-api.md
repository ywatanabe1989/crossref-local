---
description: |
  [TOPIC] HTTP API — crossref-local FastAPI server
  [DETAILS] Standalone FastAPI app in `_server/` exposing search/get/citation/collection endpoints over the local CrossRef DB. Boot with `crossref-local serve` or `uvicorn crossref_local._server:app`.
tags: [crossref-local-http-api]
---

# HTTP API — crossref-local

The `crossref_local._server` package exposes the local CrossRef DB as a
FastAPI service. Routers live alongside `__init__.py`:

- `routes_works.py` — work search + retrieval
- `routes_citations.py` — citation graph queries
- `routes_collections.py` — saved query collections
- `routes_compat.py` — legacy `/search/`, `/stats/` shim

## Endpoints

### Root / health

| Method | Path | Handler | Returns |
|--------|------|---------|---------|
| GET | `/` | root | API name, version, endpoint map |
| GET | `/health` | health | DB connectivity + path |
| GET | `/info` | info | DB statistics (work count, FTS state) |

### Works

| Method | Path | Returns |
|--------|------|---------|
| GET | `/works?q=<query>` | `SearchResponse` — FTS5 search across the corpus |
| GET | `/works/{doi:path}` | `WorkResponse` (or null) — fetch by DOI |
| POST | `/works/batch` | `BatchResponse` — bulk DOI lookup |

### Citations

| Method | Path | Returns |
|--------|------|---------|
| GET | `/citations/{doi:path}/citing` | `CitingResponse` — works that cite this DOI |
| GET | `/citations/{doi:path}/cited` | `CitedResponse` — works cited by this DOI |
| GET | `/citations/{doi:path}/count` | `CitationCountResponse` — counts only |
| GET | `/citations/{doi:path}/network` | `CitationNetworkResponse` — local graph |

### Collections

| Method | Path | Returns |
|--------|------|---------|
| GET | `/collections` | List collections |
| POST | `/collections` | Create a collection (`CollectionInfo`) |
| GET | `/collections/{name}` | Collection contents |
| GET | `/collections/{name}/stats` | Per-collection stats |
| GET | `/collections/{name}/download` | Bulk export |
| DELETE | `/collections/{name}` | Drop a collection |

### Legacy compat

| Method | Path | Notes |
|--------|------|-------|
| GET | `/search/` | Pre-`/works` search shape — kept for old clients |
| GET | `/stats/` | Pre-`/info` stats shape |

## Boot

```bash
crossref-local serve --host 0.0.0.0 --port 8765
# or
uvicorn crossref_local._server:app --port 8765
```

See `13_configuration.md` for env vars (DB path, mode, relay).
