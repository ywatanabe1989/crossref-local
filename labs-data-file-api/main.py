import sys
import inspect
import os.path
from pathlib import Path

import click
import logging

from rich import pretty
from rich.logging import RichHandler
from rich.progress import track
from rich.console import Console

FORMAT = "%(message)s"
logging.basicConfig(
    level="NOTSET",
    format=FORMAT,
    datefmt="[%X]",
    handlers=[RichHandler(console=Console(stderr=True))],
)
log = logging.getLogger("rich")

sys.path.append(
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crossrefDataFile.settings")

import django

django.setup()

from django.db import transaction
from crossrefDataFile.models import DataIndex, DataIndexWithLocation
import crossrefDataFile.api as api


@click.group()
def cli():
    pass


@click.command()
@click.option(
    "--data-directory",
    default="/home/martin/sixteenTB/April2022",
    help="The directory containing an annual Crossref data dump",
)
@transaction.atomic()
def index_all(data_directory):
    """Index all DOIs in the data directory"""
    json_items = api.iterate_all(data_directory)

    for item, file_name, location in json_items:
        DataIndex.objects.create(doi=item["DOI"], file_name=file_name)


@click.command()
@click.option(
    "--data-directory",
    default="/home/martin/sixteenTB/April2022",
    help="The directory containing an annual Crossref data dump",
)
@transaction.atomic()
def index_all_with_location(data_directory):
    """Index all DOIs in the data directory"""
    json_items = api.iterate_all(data_directory)

    for item, file_name, location in json_items:
        DataIndexWithLocation.objects.create(
            doi=item["DOI"], file_name=Path(file_name).name, location=location
        )


@click.command()
@click.option(
    "--data-directory",
    default="/home/martin/sixteenTB/April2022",
    help="The directory containing an annual Crossref data dump",
)
@click.option("--doi", help="The DOI to find")
@transaction.atomic()
def find_doi(data_directory, doi):
    """Locate a DOI in the raw files"""
    json_items = api.iterate_all(data_directory)

    for item, file_name, location in json_items:
        if item["DOI"].lower() == doi.lower():
            print(f"DOI found in {file_name}")
            return


@click.command()
@click.argument("doi")
@transaction.atomic()
def show_doi(doi):
    """Locate a DOI in the database"""
    location_row = DataIndexWithLocation.objects.get(doi__iexact=doi)
    path = Path(location_row.file_name)

    print(f"DOI {doi} found in {path}")


@click.command()
@click.option(
    "--data-directory",
    default="/home/martin/sixteenTB/April2022",
    help="The directory containing an annual Crossref data dump",
)
@click.argument("doi")
@transaction.atomic()
def lookup(data_directory, doi):
    """Return the metadata for a work from the data dump"""
    api.lookup(data_directory=data_directory, doi=doi, log=log)


@click.command()
@click.option(
    "--data-directory",
    default="/home/martin/sixteenTB/April2022",
    help="The directory containing an annual Crossref data dump",
)
@transaction.atomic()
def determine_schema(data_directory):
    """Print all fields found in the data directory"""
    all_keys = set()

    json_items = api.iterate_all(data_directory)

    for item, file_name, location in json_items:
        keys = list(item.keys())
        all_keys.update(keys)

    print(all_keys)


if __name__ == "__main__":
    cli.add_command(determine_schema)
    cli.add_command(index_all)
    cli.add_command(index_all_with_location)
    cli.add_command(lookup)
    cli.add_command(find_doi)
    cli.add_command(show_doi)
    cli()
