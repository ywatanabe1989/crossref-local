#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-15 09:28:39 (ywatanabe)"
# File: /mnt/nas_ug/crossref_local/labs-data-file-api/crossrefDataFile/app_urls.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./crossrefDataFile/app_urls.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^api/lookup/(?P<doi>.+)/$", views.lookup_doi, name="lookup_doi"),
]

# EOF
