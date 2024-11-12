# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI dependencies helper."""

import re

from pipfile import Pipfile


def rdm_version():
    """Return the latest RDM version."""
    parsed = Pipfile.load(filename="./Pipfile")

    version = parsed.data["default"].get("invenio-app-rdm", {}).get("version", "")
    if not version:
        version = parsed.data["default"].get("invenio-app-rdm", {}).get("ref", "")

    groups = re.search(
        r"[0-9]*\.[0-9]*\.[0-9]*",
        version,
    )

    if groups:
        return [int(v) for v in groups.group(0).split(".")]
    else:
        return None
