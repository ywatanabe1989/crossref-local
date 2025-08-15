import json
import logging
import sqlite3
from time import time
from typing import List

from dois2sqlite.models import Record
from dois2sqlite.representations import convert_to_common_representation

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_works_table(cursor: sqlite3.Cursor) -> None:
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS works (id INTEGER PRIMARY KEY AUTOINCREMENT, doi VARCHAR(255), resource_primary_url VARCHAR(255), type VARCHAR(255), member INTEGER, prefix VARCHAR(8), created_date_time DATE, deposited_date_time DATE, commonmeta_format BOOLEAN, metadata BLOB)"""
    )


def insert_records_into_works(cursor: sqlite3.Cursor, records: List[Record]) -> None:
    logger.info(f"Inserting {len(records):,} records")
    start_time = time()
    cursor.executemany(
        """INSERT INTO works (doi, resource_primary_url, type, member, prefix, created_date_time, deposited_date_time, commonmeta_format, metadata) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            (
                record.doi,
                record.resource_primary_url,
                record.type,
                record.member,
                record.prefix,
                record.created_date_time,
                record.deposited_date_time,
                record.commonmeta_format,
                record.metadata,
            )
            for record in records
        ],
    )
    end_time = time()
    logger.info(f"Insert took {end_time - start_time:.2f} seconds")
    logger.info("Committing")
    cursor.connection.commit()
    commit_time = time()
    logger.info(f"Commit took {commit_time - end_time:.2f} seconds")


def generate_metadata_record(item, convert_to_commonmeta) -> Record:
    converted, metadata = (
        convert_to_common_representation(item)
        if convert_to_commonmeta
        else (False, item)
    )
    return Record(
        item.get("DOI", "").lower(),
        item.get("resource", {}).get("primary", {}).get("URL", ""),
        item.get("type", ""),
        item.get("member", 0),
        item.get("prefix", ""),
        item.get("created", {}).get("date-time", ""),
        item.get("deposited", {}).get("date-time", ""),
        converted,
        json.dumps(metadata),
    )
