# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022-2025 CERN.
# Copyright (C) 2025 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI dependencies helper."""

import os
import re

try:
    import tomli as tomllib
except ModuleNotFoundError:
    import tomllib

from packaging.requirements import Requirement
from pipfile import Pipfile

_version_pattern = re.compile(r"[0-9]*\.[0-9]*\.[0-9]*")


def _parse_version(version):
    """Parse a version identifier into a list of numbers."""
    groups = _version_pattern.search(version)
    if groups:
        return [int(v) for v in groups.group(0).split(".")]
    else:
        return None


def _from_pipfile(dep_name):
    """Parse the stated dependency from the ``Pipfile``."""
    parsed = Pipfile.load(filename="./Pipfile")
    version = parsed.data.get("default", {}).get(dep_name, {}).get("version", "")
    if version == "":
        version = parsed.data.get("default", {}).get(dep_name, {}).get("ref", "")
    return _parse_version(version)


def _from_pyproject_toml(dep_name):
    """Parse the stated dependency from ``pyproject.toml``."""
    with open("./pyproject.toml", "rb") as toml_file:
        parsed = tomllib.load(toml_file)

    dependencies = [
        Requirement(d) for d in parsed.get("project", {}).get("dependencies", [])
    ]
    matched_deps = [d for d in dependencies if d.name == dep_name]
    if not matched_deps:
        return None

    # Get the first concrete positive version specifier
    v, *_ = [s for s in matched_deps[0].specifier if not s.operator.startswith("!")]
    return _parse_version(v.version)


def rdm_version():
    """Return the latest RDM version."""
    if os.path.isfile("./Pipfile"):
        return _from_pipfile("invenio-app-rdm")

    elif os.path.isfile("./pyproject.toml"):
        return _from_pyproject_toml("invenio-app-rdm")

    else:
        raise FileNotFoundError("Found neither 'Pipfile' nor 'pyproject.toml'")


def ils_version():
    """Return the latest ILS version."""
    if os.path.isfile("./Pipfile"):
        return _from_pipfile("invenio-app-ils")

    elif os.path.isfile("./pyproject.toml"):
        return _from_pyproject_toml("invenio-app-ils")

    else:
        raise FileNotFoundError("Found neither 'Pipfile' nor 'pyproject.toml'")
