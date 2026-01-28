"""Export functionality for cache module."""

import csv as _csv
import json as _json
from pathlib import Path as _Path
from typing import List, Optional

from .utils import sanitize_name as _sanitize_name

__all__ = [
    "export",
]


def _load_cache(name: str, user_id: Optional[str] = None):
    """Load cache data (lazy import to avoid circular dependency)."""
    from .cache import load

    return load(name, user_id=user_id)


def export(
    name: str,
    output_path: str,
    format: str = "json",
    fields: Optional[List[str]] = None,
    user_id: Optional[str] = None,
) -> str:
    """Export cache to file.

    Args:
        name: Cache name
        output_path: Output file path
        format: Export format (json, csv, bibtex, dois)
        fields: Fields to include (for json/csv)
        user_id: Optional user ID for multi-tenant scoping

    Returns:
        Output file path

    Raises:
        ValueError: If cache name contains invalid characters
    """
    # Validate cache name
    _sanitize_name(name)
    papers = _load_cache(name, user_id=user_id)
    output = _Path(output_path)

    if format == "json":
        if fields:
            papers = [{k: p.get(k) for k in fields} for p in papers]
        with open(output, "w") as f:
            _json.dump(papers, f, indent=2)

    elif format == "csv":
        if fields is None:
            fields = ["doi", "title", "authors", "year", "journal"]
        with open(output, "w", newline="") as f:
            writer = _csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            for p in papers:
                row = dict(p)
                if "authors" in row and isinstance(row["authors"], list):
                    row["authors"] = "; ".join(row["authors"])
                writer.writerow(row)

    elif format == "bibtex":
        lines = []
        for p in papers:
            doi = p.get("doi", "").replace("/", "_").replace(".", "_")
            entry = f"@article{{{doi},\n"
            if p.get("title"):
                entry += f"  title = {{{p['title']}}},\n"
            if p.get("authors"):
                authors = (
                    " and ".join(p["authors"])
                    if isinstance(p["authors"], list)
                    else p["authors"]
                )
                entry += f"  author = {{{authors}}},\n"
            if p.get("year"):
                entry += f"  year = {{{p['year']}}},\n"
            if p.get("journal"):
                entry += f"  journal = {{{p['journal']}}},\n"
            if p.get("doi"):
                entry += f"  doi = {{{p['doi']}}},\n"
            entry += "}\n"
            lines.append(entry)
        with open(output, "w") as f:
            f.write("\n".join(lines))

    elif format == "dois":
        dois = [p["doi"] for p in papers if p.get("doi")]
        with open(output, "w") as f:
            f.write("\n".join(dois))

    else:
        raise ValueError(f"Unknown format: {format}")

    return str(output)
