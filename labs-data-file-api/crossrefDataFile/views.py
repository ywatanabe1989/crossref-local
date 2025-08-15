#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-15 09:20:53 (ywatanabe)"
# File: /mnt/nas_ug/crossref_local/labs-data-file-api/crossrefDataFile/views.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./crossrefDataFile/views.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

from pathlib import Path

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .api import fetch_work
from .models import DataIndex, DataIndexWithLocation


@csrf_exempt
def lookup_doi(request, doi):
    data_directory = "/home/martin/sixteenTB/April2022"

    try:
        location_row = DataIndexWithLocation.objects.get(doi__iexact=doi)
        path = Path(data_directory) / Path(location_row.file_name)
        work = fetch_work(
            doi=doi, gzip_file=path, location=location_row.location
        )
        return JsonResponse(work)
    except DataIndexWithLocation.DoesNotExist:
        try:
            location_row = DataIndex.objects.get(doi__iexact=doi)
            path = Path(data_directory) / Path(location_row.file_name)
            work = fetch_work(doi=doi, gzip_file=path, location=None)
            return JsonResponse(work)
        except DataIndex.DoesNotExist:
            return JsonResponse({"error": "DOI not found"}, status=404)

# EOF
