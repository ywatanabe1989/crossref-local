#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-14 05:35:36 (ywatanabe)"
# File: /mnt/nas_ug/crossref_local/dois2sqlite/dois2sqlite/cli.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./dois2sqlite/cli.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

import logging
import sqlite3
import tarfile
# from itertools import batched
from pathlib import Path
from time import time
from typing import List

import typer
from joblib import Parallel, delayed

from dois2sqlite.database import create_works_table, insert_records_into_works
from dois2sqlite.file_handlers import (collect_and_categorize_json_files,
                                       get_json_files_in_tar)
from dois2sqlite.utils import get_cpu_count

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = typer.Typer(
    help="Tool for loading Crossref metadata into a SQLite database"
)

VERBOSE_HELP = "Verbose mode"
PARALLEL_PREFER = "processes"
DEFAULT_COMMIT_SIZE = 500000


from itertools import islice


def batched(iterable, nn):
    iterator = iter(iterable)
    while chunk := list(islice(iterator, nn)):
        yield chunk


def process_json_files_and_insert_records(
    json_files,
    create_records_func,
    src_path,
    sqlite_path,
    n_jobs,
    commit_size,
    dry_run,
    convert_to_commonmeta,
) -> int:
    total_records = 0
    with sqlite3.connect(sqlite_path) as conn:
        cursor = conn.cursor()
        commit_batch: List = []
        for file_batch in batched(json_files, n_jobs):
            results = Parallel(n_jobs=n_jobs, prefer=PARALLEL_PREFER)(
                delayed(create_records_func)(
                    json_file, src_path, convert_to_commonmeta
                )
                for json_file in file_batch
            )
            commit_batch.extend(
                item for sublist in results for item in sublist
            )
            if len(commit_batch) >= commit_size:
                total_records += len(commit_batch)
                if not dry_run:
                    insert_records_into_works(cursor, commit_batch)
                logger.info(f"Current total: {total_records:,}")
                commit_batch = []

        if commit_batch and not dry_run:
            insert_records_into_works(cursor, commit_batch)
            total_records += len(commit_batch)

    return total_records


@app.command()
def create(
    sqlite_path: Path = typer.Argument(..., exists=False),
    verbose: bool = typer.Option(False, help=VERBOSE_HELP),
) -> None:
    """
    Create a new SQLite database at the specified path.
    """
    if verbose:
        logger.setLevel(logging.INFO)
        logger.info("Verbose mode")

    with sqlite3.connect(sqlite_path) as conn:
        cursor = conn.cursor()
        create_works_table(cursor)
    logger.info(f"Database created at {sqlite_path}")


@app.command()
def load(
    src_path: Path = typer.Argument(..., exists=True),
    sqlite_path: Path = typer.Argument(..., exists=True),
    n_jobs: int = typer.Option(1, help="Number of jobs"),
    commit_size: int = typer.Option(
        DEFAULT_COMMIT_SIZE, help="Number of records to commit at a time"
    ),
    verbose: bool = typer.Option(False, help=VERBOSE_HELP),
    dry_run: bool = typer.Option(
        False,
        help="Dry run. Does everything except the actual insert into the database.",
    ),
    max_files: int = typer.Option(
        None, help="Maximum number of files to process"
    ),
    convert_to_commonmeta: bool = typer.Option(
        False, help="Convert to commonmeta"
    ),
    clobber_sqlite: bool = typer.Option(
        False, help="Clobber the SQLite database, if it already exists"
    ),
) -> None:
    """
    Load data from a src into SQLite.
    """
    if verbose:
        logger.setLevel(logging.INFO)
        logger.info("Verbose mode")

    jason_files, create_records_func = collect_and_categorize_json_files(
        src_path, max_files
    )
    total_records = process_json_files_and_insert_records(
        jason_files,
        create_records_func,
        src_path,
        sqlite_path,
        n_jobs,
        commit_size,
        dry_run,
        convert_to_commonmeta,
    )

    logger.info(
        f"Done: {total_records:,} records loaded from {src_path} into {sqlite_path}"
    )


@app.command()
def index(
    sqlite_path: Path = typer.Argument(..., exists=True),
    verbose: bool = typer.Option(False, help=VERBOSE_HELP),
) -> None:
    """
    Create indexes on an existing SQLite database.
    """
    if verbose:
        logger.setLevel(logging.INFO)
        logger.info("Verbose mode")

    with sqlite3.connect(sqlite_path) as conn:
        cursor = conn.cursor()
        indexes = [
            "doi",
            # "resource_primary_url",
            "type",
            "member",
            "prefix",
            "created_date_time",
            "deposited_date_time",
            "commonmeta_format",
        ]
    for index in indexes:
        logger.info(f"Creating index on {index}")
        start_time = time()
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{index} ON works ({index})"
        )
        logger.info(f"Index on {index} took {time() - start_time:.2f} seconds")
    logger.info("Committing indexes")
    start_time = time()
    cursor.connection.commit()
    logger.info(f"Index commit took {time() - start_time:.2f} seconds")
    logger.info(f"Indexes created on the database at {sqlite_path}")


@app.command()
def tarinfo(
    tar_path: Path = typer.Argument(..., exists=True),
    verbose: bool = typer.Option(False, help=VERBOSE_HELP),
) -> None:
    """
    Analyze the TAR file and print out information about it, including the following:

    - The number of JSON files in the TAR file
    - The estimated number of work items in total

    """
    if verbose:
        logger.setLevel(logging.INFO)
        logger.info("Verbose mode")

    with tarfile.open(tar_path, "r") as tar_file:
        # print(tarfile.TarInfo.name)
        # number_of_files = len(json_files_in_tar(tar_file))
        number_of_files = len(get_json_files_in_tar(tarfile.TarInfo.name))

        estimated_number_of_items = number_of_files * 5000
        print(f"Number of files: {number_of_files}")
        print(f"Estimated number of items: {estimated_number_of_items:,}")
        print(f"Recommended cores: {get_cpu_count()}")


if __name__ == "__main__":
    app()

# EOF
