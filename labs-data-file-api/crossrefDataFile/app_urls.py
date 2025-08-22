#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-22 19:07:38 (ywatanabe)"
# File: /mnt/nas_ug/crossref_local/labs-data-file-api/crossrefDataFile/app_urls.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./labs-data-file-api/crossrefDataFile/app_urls.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^api/search/$", views.search, name="search"),
]

# urlpatterns = [
#     re_path(r"^api/lookup/(?P<doi>.+)/$", views.lookup_doi, name="lookup_doi"),
#     re_path(r"^api/search/title/$", views.search_title, name="search_title"),
# ]

# EOF
