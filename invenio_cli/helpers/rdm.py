# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI dependencies helper."""

import re

from ..helpers.cli_config import CLIConfig


def rdm_version():
    """Return the latest RDM version."""
    cliConfig = CLIConfig()
    if (cliConfig.project_path / "Pipfile").is_file():
        depfile = cliConfig.project_path / "Pipfile"
    elif (cliConfig.project_path / "pyproject.toml").is_file():
        depfile = cliConfig.project_path / "pyproject.toml"

    match = re.search(
        r"invenio-app-rdm.*?==([\d.]+(?:b\d+)?(?:\.dev\d+)?)",
        depfile.read_text(),
    )

    if match:
        print(match.group(1))
        apprdmversion = []
        for v in match.group(1).split("."):

            try:
                vs = int(v)
                apprdmversion.append(vs)
            except ValueError:
                apprdmversion.append(v)
        print("Invenio RDM version: ", apprdmversion)
        return apprdmversion
    else:
        return None
