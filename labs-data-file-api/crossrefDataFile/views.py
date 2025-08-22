#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-22 19:33:09 (ywatanabe)"
# File: /mnt/nas_ug/crossref_local/labs-data-file-api/crossrefDataFile/views.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./labs-data-file-api/crossrefDataFile/views.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .api import fetch_work, search_by_metadata, search_by_title
from .models import DataIndex, DataIndexWithLocation


@csrf_exempt
def search(request):
    doi = request.GET.get("doi")
    title = request.GET.get("title")
    year = request.GET.get("year")
    authors = request.GET.get("authors")

    if doi:
        work = fetch_work(doi)
        if work:
            return JsonResponse(work)
        return JsonResponse({"error": "DOI not found"}, status=404)

    if title or year or authors:
        results = search_by_metadata(title=title, year=year, authors=authors)
        return JsonResponse({"results": results})

    return JsonResponse(
        {"error": "Specify doi, title, year, or authors parameter"}, status=400
    )


# @csrf_exempt
# def search(request):
#     doi = request.GET.get("doi")
#     title = request.GET.get("title")

#     if doi:
#         work = fetch_work(doi)
#         if work:
#             return JsonResponse(work)
#         return JsonResponse({"error": "DOI not found"}, status=404)

#     if title:
#         results = search_by_title(title)
#         return JsonResponse({"results": results})

#     return JsonResponse(
#         {"error": "Specify either doi or title parameter"}, status=400
#     )


# @csrf_exempt
# def lookup_doi(request, doi):
#     try:
#         work = fetch_work(doi)
#         if work is None:
#             return JsonResponse({"error": "DOI not found"}, status=404)
#         return JsonResponse(work)
#     except Exception:
#         return JsonResponse({"error": "DOI not found"}, status=404)


# @csrf_exempt
# def search_title(request):
#     title = request.GET.get("q", "")
#     if not title:
#         return JsonResponse(
#             {"error": "Missing title query parameter 'q'"}, status=400
#         )

#     results = search_by_title(title)
#     return JsonResponse({"results": results})


# @csrf_exempt
# def lookup_doi(request, doi):
#     data_directory = "../data/March 2025 Public Data File from Crossref"
#     # data_directory = "/home/martin/sixteenTB/April2022"

#     try:
#         location_row = DataIndexWithLocation.objects.get(doi__iexact=doi)
#         path = Path(data_directory) / Path(location_row.file_name)
#         work = fetch_work(
#             doi=doi, gzip_file=path, location=location_row.location
#         )
#         return JsonResponse(work)
#     except DataIndexWithLocation.DoesNotExist:
#         try:
#             location_row = DataIndex.objects.get(doi__iexact=doi)
#             path = Path(data_directory) / Path(location_row.file_name)
#             work = fetch_work(doi=doi, gzip_file=path, location=None)
#             return JsonResponse(work)
#         except DataIndex.DoesNotExist:
#             return JsonResponse({"error": "DOI not found"}, status=404)

# EOF
