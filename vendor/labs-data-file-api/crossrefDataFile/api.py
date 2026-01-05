#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-22 19:37:47 (ywatanabe)"
# File: /mnt/nas_ug/crossref_local/labs-data-file-api/crossrefDataFile/api.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./labs-data-file-api/crossrefDataFile/api.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

import gzip
import json
import logging
import tarfile
from pathlib import Path

from rich.progress import track

from crossrefDataFile.models import DataIndex, DataIndexWithLocation


def iterate_all(data_directory) -> (dict, str, int):
    """Iterate over all DOIs in the data directory"""
    data_path = Path(data_directory)
    gz_files = list(data_path.glob("*.gz"))

    # determine if this is single file or distributed
    plus = len(gz_files) == 1

    if not plus:
        logging.info("Loading public data dump")
        # for file in track(gz_files):
        #     with gzip.open(file, 'rt') as f_handle:
        #         contents = f_handle.read()
        #         json_contents = json.loads(contents)
        #         location = 0

        #         for json_item in json_contents['items']:
        #             yield json_item, file, location

        #             location = location + 1

        for file in track(gz_files):
            with gzip.open(file, "rt") as f_handle:
                location = 0
                for line in f_handle:
                    line = line.strip()
                    if line:
                        json_item = json.loads(line)
                        yield json_item, file, location
                        location = location + 1

    else:
        logging.info("Loading Plus data dump")
        for file in gz_files:

            with tarfile.open(file, "r:gz") as tarf:

                for member in track(tarf):
                    with tarf.extractfile(member) as f_handle:
                        contents = f_handle.read()
                        json_contents = json.loads(contents)

                        location = 0

                        for json_item in json_contents["items"]:
                            yield json_item, file, location

                            location = location + 1


def fetch_work(doi):
    try:
        data_entry = DataIndexWithLocation.objects.get(doi=doi)
    except DataIndexWithLocation.DoesNotExist:
        return None

    data_directory = "../data/March 2025 Public Data File from Crossref"
    file_path = os.path.join(data_directory, data_entry.file_name)

    with gzip.open(file_path, "rt") as file_:
        line_number = 0
        for line in file_:
            if line_number == data_entry.location:
                line = line.strip()
                if line:
                    return json.loads(line)
                return None
            line_number += 1

    return None


def search_by_title(title_query, limit=10):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT doi FROM crossrefDataFile_dataindexwithlocation
            WHERE doi IN (
                SELECT doi FROM crossrefDataFile_dataindexwithlocation
                LIMIT 1000
            )
        """
        )

        results = []
        for row in cursor.fetchall():
            work = fetch_work(row[0])
            if work and "title" in work:
                for work_title in work["title"]:
                    if title_query.lower() in work_title.lower():
                        results.append(
                            {"doi": work["DOI"], "title": work_title}
                        )
                        if len(results) >= limit:
                            return results

        return results


def lookup(data_directory, doi, log=None):
    """Return the metadata for a work from the data dump"""

    # lookup order:
    # 1. Index with location
    # 2. Index without location
    # 3. Sequential non-indexed lookup (TODO)

    work = None

    try:
        location_row = DataIndexWithLocation.objects.get(doi=doi)
        path = Path(data_directory) / Path(location_row.file_name)
        work = fetch_work(
            doi=doi, gzip_file=path, location=location_row.location
        )
    except DataIndexWithLocation.DoesNotExist:
        _log_info(
            log=log,
            message="Unable to find location-based index. "
            "Attempting to use file-based index.",
        )
        try:
            location_row = DataIndex.objects.get(doi=doi)
            path = Path(data_directory) / Path(location_row.file_name)
            work = fetch_work(doi=doi, gzip_file=path, location=None)
        except DataIndex.DoesNotExist:
            _log_info(
                log=log,
                message="Unable to find file-based index. "
                "Attempting to use sequential lookup.",
            )

    _log_info(log=log, message=work)
    return work


def _log_info(log, message):
    """Log information to the console (stdout)"""
    if log:
        log.info(message)


def _log_error(log, message):
    """Log errors to the console (stderr)"""
    if log:
        log.error(message)


def search_by_metadata(title=None, year=None, authors=None, limit=10):
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT doi FROM crossrefDataFile_dataindexwithlocation
            LIMIT 5000
        """
        )

        results = []
        for row in cursor.fetchall():
            work = fetch_work(row[0])
            if not work:
                continue

            matches = True

            if title and "title" in work:
                title_match = any(
                    title.lower() in work_title.lower()
                    for work_title in work["title"]
                )
                matches = matches and title_match

            if year:
                year_match = False
                if (
                    "published-print" in work
                    and "date-parts" in work["published-print"]
                ):
                    if work["published-print"]["date-parts"]:
                        work_year = work["published-print"]["date-parts"][0][0]
                        year_match = str(work_year) == str(year)
                elif (
                    "published-online" in work
                    and "date-parts" in work["published-online"]
                ):
                    if work["published-online"]["date-parts"]:
                        work_year = work["published-online"]["date-parts"][0][
                            0
                        ]
                        year_match = str(work_year) == str(year)
                elif "issued" in work and "date-parts" in work["issued"]:
                    if work["issued"]["date-parts"]:
                        work_year = work["issued"]["date-parts"][0][0]
                        year_match = str(work_year) == str(year)
                matches = matches and year_match

            if authors and "author" in work:
                authors_list = [
                    auth.strip().lower() for auth in authors.split(",")
                ]
                author_match = any(
                    any(
                        auth_query
                        in f"{author.get('given', '')} {author.get('family', '')}".lower()
                        for author in work["author"]
                    )
                    for auth_query in authors_list
                )
                matches = matches and author_match

            if matches:
                result = {"doi": work["DOI"]}
                if "title" in work and work["title"]:
                    result["title"] = work["title"][0]
                if (
                    "published-print" in work
                    and "date-parts" in work["published-print"]
                ):
                    if work["published-print"]["date-parts"]:
                        result["year"] = work["published-print"]["date-parts"][
                            0
                        ][0]
                if "author" in work:
                    result["authors"] = [
                        f"{author.get('given', '')} {author.get('family', '')}"
                        for author in work["author"][:3]
                    ]
                results.append(result)

                if len(results) >= limit:
                    break

        return results

# EOF
