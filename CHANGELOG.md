# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-01-11

### Added
- CLI `-a/--with-abstracts` flag to display abstracts in search results
- Composed README figure combining IF validation and citation network
- Citation network visualization using figrecipe graph()
- GitHub Actions CI workflow
- Binder support for interactive notebooks
- Async API (`crossref_local.aio`)

### Changed
- Simplified README with collapsible sections
- Improved figure sizing for consistency (40x28mm)
- White backgrounds for all figures

### Fixed
- Figure margins for consistent sizing
- `fig.savefig` for proper white backgrounds

## [0.2.0] - 2026-01-10

### Added
- Impact factor validation examples with JCR comparison
- OpenAlex-based journal lookup for fast ISSN resolution
- SciTeX branding and AGPL-3.0 license

### Changed
- Moved validation figure to top of README

## [0.1.0] - 2026-01-09

### Added
- Initial release
- Core Python API: `search()`, `get()`, `count()`, `exists()`, `info()`
- Full-text search via FTS5 across 167M+ records
- Impact factor calculation from citation data
- Citation network analysis (`get_citing()`, `get_cited()`, `CitationNetwork`)
- CLI with commands: search, get, count, info, impact-factor
- Command aliases (s, g, c, i, if)

<!-- EOF -->
