import sys
import typer
import json
import requests
from collections import Counter, defaultdict
from pathlib import Path
from cnserver.settings import SUPPORTED_MEDIA_TYPES
from cnserver.cslutils import list_citation_styles, list_citation_locales
from cnserver.accept_header_utils import parse_accept_header
csl_styles = list_citation_styles("cnserver/styles")
csl_locales = list_citation_locales("cnserver/locales")


CN_API = "http://dx.doi.org"
#CN_API = "http://localhost:8000"
BIBLIO_CITATION = "text/x-bibliography;" 
popular_csl = ["apa","harvard1","ieee","vancouver"]
popular_locales = ["en-US","fr-FR","de-DE","es-ES"]


def get_result(doi,header, api_url):
    return requests.get(f"{api_url}/{doi}", headers={"Accept": header})

def show_result(doi, header, result):
    print(f"### Accept: {header}")
    print (f"### Status: {result.status_code}")
    print(f"""
          ```
          {result.text}
          ```
          """)
    
    print("="*80)


def main(doi_list_path: Path = typer.Argument(..., exists=True), api_url: str = typer.Option(default="http://localhost:8000")) -> None:


    with open(doi_list_path, "r") as f:
            dois = f.readlines()

    test_count = 0
    status_counts_per_header = defaultdict(Counter)
    for doi in dois:
        doi = doi.strip()
        print(f"## DOI: {doi}")
        for media_type in SUPPORTED_MEDIA_TYPES:
            header = media_type
            if media_type == "text/x-bibliography":
                
                for style in popular_csl:
                    for locale in popular_locales:
                        header = f"{media_type}; style={style}; locale={locale}"
                        result = get_result(doi,header, api_url=api_url)
                        status_counts_per_header[header][result.status_code] += 1
                        show_result(doi,header,result)
                        
                        test_count += 1
                continue
            result = get_result(doi,header, api_url=api_url)
            status_counts_per_header[header][result.status_code] += 1
            show_result(doi,header,result)
            test_count += 1

    print(f"Ran {test_count} tests")
    print("="*80)
    print("## Error Summary")
    for header, status_counts in status_counts_per_header.items():
        print(f"Results for Accept: {header}")
        for status, count in status_counts.items():
            print(f"Status {status}: {count}")
        print("="*80)

if __name__ == "__main__":
    typer.run(main)







