from dataclasses import dataclass


@dataclass
class Record:
    doi: str
    resource_primary_url: str
    type: str
    member: int
    prefix: str
    created_date_time: str
    deposited_date_time: str
    commonmeta_format: bool
    metadata: str
