---
name: crossref-local-env-vars
description: Environment variables read by crossref-local at import / runtime. Follow SCITEX_<MODULE>_* convention — see general/10_arch-environment-variables.md.
tags: [crossref-local, scitex-package]
---

# crossref-local — Environment Variables

All vars use the upstream `SCITEX_SCHOLAR_CROSSREF_*` prefix because
crossref-local ships the CrossRef backend for scitex-scholar (the vars were
coined there and kept stable for back-compat).

| Variable | Purpose | Default | Type |
|---|---|---|---|
| `SCITEX_SCHOLAR_CROSSREF_DB` | Path to the local CrossRef SQLite DB (167M+ works). | `~/.scitex/scholar/crossref/works.db` | path |
| `SCITEX_SCHOLAR_CROSSREF_MODE` | Backend mode: `local` (read SQLite directly), `remote` (HTTP to a daemon), or `auto`. | `auto` | string |
| `SCITEX_SCHOLAR_CROSSREF_HOST` | Hostname of the remote daemon (used when `MODE=remote`). | `localhost` | string |
| `SCITEX_SCHOLAR_CROSSREF_PORT` | Port of the remote daemon. | `8765` | int |

## Feature flags

None. All vars are configuration values.

## Notes

- When `SCITEX_SCHOLAR_CROSSREF_MODE=auto`, crossref-local probes the SQLite
  path first and falls back to the remote daemon if the file is missing.
- These vars are shared with scitex-scholar; set them once in the user
  environment and both packages will honor them.

## Audit

```bash
grep -rhoE 'SCITEX_[A-Z0-9_]+' $HOME/proj/crossref-local/src/ | sort -u
```
