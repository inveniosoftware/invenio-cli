# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022 CERN.
# Copyright (C) 2025 Graz University of Technology.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI dependencies helper."""

import importlib
import re


def rdm_version():
    """Return the latest RDM version."""
    version = importlib.metadata.version("invenio-app-rdm")
    groups = re.search(r"[0-9]*\.[0-9]*\.[0-9]*", version)

    if groups:
        return [int(v) for v in groups.group(0).split(".")]

    return None
