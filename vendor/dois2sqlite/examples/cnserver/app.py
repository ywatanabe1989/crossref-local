import logging
from fastapi import FastAPI, Header, HTTPException, Response
from typing import AsyncGenerator, Dict, Optional
from pathlib import Path
import sqlite3
import sys
import json
#from commonmeta.readers.commonmeta import commonmeta_read
from commonmeta import Metadata

from cnserver.accept_header_utils import parse_accept_header
from cnserver.settings import SUPPORTED_MEDIA_TYPES, MEDIA_TYPE_TO_NAME
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

db = None

app = FastAPI()

def ensure_path_exists(path: Path):
    return path.exists()
        



    
async def get_metadata(doi: str) -> str:
    # lookup doi in database and and get the metadata column
    # if doi is not found, return 404
    # if doi is found, return the metadata
    cursor = db.cursor()
    cursor.execute("SELECT metadata FROM works WHERE doi = ?", (doi,))
    row = cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"DOI {doi} not found")
    return row[0]

def is_supported_media_type(media_type: str) -> bool:
    return media_type in SUPPORTED_MEDIA_TYPES

async def content_types(accept: str) -> dict | None:
    parsed_accept = parse_accept_header(accept)
    for media_type in parsed_accept:
        logger.info(f"Checking if media type {media_type['media_type']} is supported")
        if is_supported_media_type(media_type['media_type']):
            logger.info(f"Media type {media_type['media_type']} is supported")
            return {    
                'media_type': media_type['media_type'],
                #'style': media_type['parameters']['style'],
                # style, if it exists, otherwise None
                'style': media_type['parameters'].get('style', None),
                # 'locale': media_type['parameters']['locale']
                # locale, if it exists, otherwise None
                'locale': media_type['parameters'].get('locale', None)
            }
    logger.info("No supported media type found")
    return None

async def get_representation(doi: str, accept: str) -> str:
    logger.info(f"Getting representation for DOI {doi} with Accept: {accept}")
    parsed_accept = parse_accept_header(accept)
    logger.info(f"Parsed Accept header: {parsed_accept}")
    logger.info("Checking if the accept header is supported")
    supported_content_type = await content_types(accept)
    if supported_content_type is None:
        raise HTTPException(status_code=406, detail="Not Acceptable")
    logger.info(f"Supported content type: {supported_content_type}")
    logger.info("Getting metadata")
    representation_func = MEDIA_TYPE_TO_NAME[supported_content_type['media_type']]
    metadata = await get_metadata(doi)
    logger.info("Metadata retrieved")
    logger.info("Rendering representation")
    try:
        metadata = Metadata(metadata)
        logger.info(f"Rendering representation using: {representation_func}")
        if f"{representation_func}" == "citation":
            metadata.style = supported_content_type['style']
            metadata.locale = supported_content_type['locale']
            
        # dynamically call the representation function on the metadata object
        representation = getattr(metadata, representation_func)()
        logger.info(f"Returning representation: {representation}")
        return representation
    except Exception as e:
        logger.error(f"Error rendering representation: {e}")
        raise HTTPException(status_code=406, detail=f"Not Acceptable: {accept}") from e
    





@app.get("/{doi:path}")
async def cn(doi: str, accept: Optional[str] = Header(None)):
    if accept is None:
        raise HTTPException(status_code=400, detail="Accept header is required")
    
    representation = await get_representation(doi, accept)
    
    #return json.dumps(representation, indent=4)
    # return representation and set the content type to the media type
    return Response(content=representation, media_type=accept)

    

if __name__ == "__main__":
    import uvicorn
    db_path = Path(sys.argv[1])
    if not ensure_path_exists(db_path):
        print(f"Path {db_path} does not exist", file=sys.stderr)
        sys.exit(1)
    db = sqlite3.connect(db_path)


    uvicorn.run(app, host="0.0.0.0", port=8000)
