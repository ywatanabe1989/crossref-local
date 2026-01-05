<!-- ---
!-- Timestamp: 2025-08-22 19:09:35
!-- Author: ywatanabe
!-- File: /mnt/nas_ug/crossref_local/labs-data-file-api/README.md
!-- --- -->


# Debugging

```python
# python manager.py shell
from crossrefDataFile.models import DataIndexWithLocation
from pprint import pprint
print(DataIndexWithLocation.objects.filter(doi__icontains="10.1001").count()) # 587811
print(DataIndexWithLocation.objects.filter(doi="10.1001/.387").exists()) # True
print(DataIndexWithLocation.objects.filter(doi__icontains="10.1001").values('doi', 'file_name')[:5])
# <QuerySet [{'doi': '10.1001/jama.2024.24064', 'file_name': '387.jsonl.gz'}, {'doi': '10.1001/jamapsychiatry.2015.2732', 'file_name': '18488.jsonl.gz'}, {'doi': '10.1001/jamapsychiatry.2015.2964', 'file_name': '18488.jsonl.gz'}, {'doi': '10.1001/jamasurg.2015.5116', 'file_name': '18488.jsonl.gz'}, {'doi': '10.1001/jamasurg.2015.5233', 'file_name': '18488.jsonl.gz'}]>

# Usage:
# curl "http://127.0.0.1:3333/api/search/?doi=10.1001/.387"
# curl "http://127.0.0.1:3333/api/search/?title=medicine"
```

# API for Interacting with the Crossref Annual Data File
A python API for interacting with the Crossref Annual Data File dump.

![license](https://img.shields.io/gitlab/license/crossref/labs/labs-data-file-api) ![activity](https://img.shields.io/gitlab/last-commit/crossref/labs/labs-data-file-api)

![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![Git](https://img.shields.io/badge/git-%23F05033.svg?style=for-the-badge&logo=git&logoColor=white) ![GitHub](https://img.shields.io/badge/github-%23121011.svg?style=for-the-badge&logo=github&logoColor=white) ![Linux](https://img.shields.io/badge/Linux-FCC624?style=for-the-badge&logo=linux&logoColor=black) ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

This command-line application allows you to build various indexes for working with the annual data dump from Crossref.

This tool is an experimental project from Crossref Labs, provided without warranty or support. 

    Usage: main.py [OPTIONS] COMMAND [ARGS]...

    Options:
      --help  Show this message and exit.
    
    Commands:
      determine-schema         Print all fields found in the data directory
      find-doi                 Locate a DOI in the raw files
      index-all                Index all DOIs in the data directory
      index-all-with-location  Index all DOIs in the data directory
      lookup                   Return the metadata for a work from the data dump
      show-doi                 Locate a DOI in the database



## Features
* Build index of DOI -> gzip location
* Build precise index of DOI -> gzip location -> DOI offset
* Extract schema definitions from the dataset

# Usage

## determine-schema
The determine-schema command scans the entire compressed JSON archive and extracts all keys that are present. This is useful when you want to know which fields are available across the entire dataset, particularly when schema versions change. This information is, of course, available in the schema definitions, but this command allows for its reconstruction from the raw data.

On our test machine, creating the index-all index took approximately 4.5 hours to run.

## index-all
The index-all command builds an index in your specified database format that allows for on-disk lookup of a Work by DOI from the compressed data store.

For instance, an index entry here may contain: 10.1017/s0336930602210180 / 138.json.gz.

Querying the filestore for 10.1017/s0336930602210180 will, using index-all, require a maximum read of 5,000 JSON entries from 138.json.gz. This is typically fast enough for most users and balances storage space against retrieval time.

On our test machine, creating the index-all index took approximately 7.5 hours and consumed 11.4GB of disk space.

## index-all-with-location
The index-all-with-location command builds an index in your specified database format that allows for on-disk lookup of a Work by DOI from the compressed data store.

For instance, an index entry here may contain: 10.1017/s0336930602210180 / 138.json.gz / 456.

Querying the filestore for 10.1017/s0336930602210180 will, using index-all-with-location, require a maximum iteration of 1 JSON entry from 138.json.gz. Because this method stores the precise offset at which the DOI is stored, it allows for marginally faster lookups than index-all. This is a useful index when you will be performing many queries on the filestore.

On our test machine, creating the index-all-with-location index took approximately 8 hours and consumed 12.4GB of disk space.

## Prerequisites
Before building the database of indexes you must initialize it:

    python3 manage.py migrate

You can adjust the database settings in settings.py.

## Torrent

[A torrent is available for the index](https://academictorrents.com/details/674d3fbbca65c46c0ba52a65658aef0c8fc99e86) in SQLite format if you do not wish to generate it yourself.

# Credits
* [Django](https://www.djangoproject.com/) for the ORM.
* [Git](https://git-scm.com/) from Linus Torvalds _et al_.
* [.gitignore](https://github.com/github/gitignore) from Github.
* [Rich](https://github.com/Textualize/rich) from Textualize.

&copy; Crossref 2024

<!-- EOF -->