#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-14 05:26:21 (ywatanabe)"
# File: /mnt/nas_ug/crossref_local/dois2sqlite/dois2sqlite/file_handlers.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./dois2sqlite/file_handlers.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

import gzip
import json
import logging
import tarfile
from pathlib import Path
from time import time
from typing import Callable, List, Tuple

from dois2sqlite.database import generate_metadata_record
from dois2sqlite.models import Record

TEMP_DIR = "/tmp/cr-records"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_items_from_json(file_name: str) -> List[dict]:
    with open(file_name, "rb") as f:
        return json.load(f)["items"]


def get_json_files_in_tar(src_path: str) -> List[str]:
    with tarfile.open(src_path, "r") as tar:
        return [
            member.name
            for member in tar.getmembers()
            if member.isfile() and member.name.endswith(".json")
        ]


def generate_records_from_tar(
    file_name, tar_file_path, convert_to_commonmeta
) -> List[Record]:
    logger.info(f"Extracting records from: {file_name}")
    start_time = time()
    with tarfile.open(tar_file_path) as tar:
        member = tar.getmember(file_name)
        fn = Path(TEMP_DIR, member.name)

        tar.extract(member, path=TEMP_DIR)

        records = [
            generate_metadata_record(item, convert_to_commonmeta)
            for item in load_items_from_json(fn)
        ]
        fn.unlink()

    end_time = time()
    logger.info(
        f"Extracted {len(records):,} records from {file_name} in {end_time - start_time:.2f} seconds"
    )
    return records


def generate_records_from_compressed_json(
    compressed_json_file, _, convert_to_commonmeta
) -> List[Record]:
    logger.info(f"Extracting records from: {compressed_json_file}")
    start_time = time()
    with gzip.open(compressed_json_file, "rb") as f:
        records = [
            generate_metadata_record(item, convert_to_commonmeta)
            for item in json.load(f)["items"]
        ]
    end_time = time()
    logger.info(
        f"Extracted {len(records):,} records from {compressed_json_file} in {end_time - start_time:.2f} seconds"
    )
    return records


# def collect_and_categorize_json_files(
#     src_path, max_files
# ) -> Tuple[List[str], Callable]:
#     if src_path.is_dir():
#         json_files = (
#             list(src_path.glob("*.json.gz"))[:max_files]
#             if max_files
#             else list(src_path.glob("*.json.gz"))
#         )
#         create_records_func = generate_records_from_compressed_json
#     else:  # Assuming src_path is a file
#         json_files = (
#             get_json_files_in_tar(str(src_path))[:max_files]
#             if max_files
#             else get_json_files_in_tar(str(src_path))
#         )
#         create_records_func = generate_records_from_tar
#     return json_files, create_records_func


def generate_records_from_compressed_jsonl(
    compressed_jsonl_file, _, convert_to_commonmeta
) -> List[Record]:
    logger.info(f"Extracting records from: {compressed_jsonl_file}")
    start_time = time()

    records = []
    with gzip.open(compressed_jsonl_file, "rt") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                records.append(
                    generate_metadata_record(item, convert_to_commonmeta)
                )

    end_time = time()
    logger.info(
        f"Extracted {len(records):,} records from {compressed_jsonl_file} in {end_time - start_time:.2f} seconds"
    )
    return records


def collect_and_categorize_json_files(
    src_path, max_files
) -> Tuple[List[str], Callable]:
    if src_path.is_dir():
        json_files = (
            list(src_path.glob("*.jsonl.gz"))[:max_files]
            if max_files
            else list(src_path.glob("*.jsonl.gz"))
        )
        create_records_func = generate_records_from_compressed_jsonl
    else:
        json_files = (
            get_json_files_in_tar(str(src_path))[:max_files]
            if max_files
            else get_json_files_in_tar(str(src_path))
        )
        create_records_func = generate_records_from_tar
    return json_files, create_records_func

# EOF
