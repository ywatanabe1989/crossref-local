#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-15 09:31:10 (ywatanabe)"
# File: /mnt/nas_ug/crossref_local/labs-data-file-api/crossrefDataFile/wsgi.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./crossrefDataFile/wsgi.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------
"""
WSGI config for preservationData project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/wsgi/
"""

from django.core.wsgi import get_wsgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'preservationData.settings')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crossrefDataFile.settings")

application = get_wsgi_application()

# EOF
