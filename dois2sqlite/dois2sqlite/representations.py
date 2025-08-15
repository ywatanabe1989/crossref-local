import logging
from typing import List, Tuple

from commonmeta.readers.crossref_reader import read_crossref

from dois2sqlite.models import Record

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def convert_to_common_representation(item) -> Tuple[bool, List[str]]:
    try:
        commonmeta = read_crossref(item)
        return True, commonmeta
    except Exception as e:
        logger.error(
            f"Error converting to commonmeta: DOI:{item.get('DOI', '').lower()}: {type(e)}: {e}"
        )

        return False, item
