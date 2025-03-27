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

    # find invenio-app-rdm line in either file
    matchline = re.search(r"^.?invenio-app-rdm.*$", depfile.read_text(), re.MULTILINE)

    # extract the version number of invenio-app-rdm
    if matchline:
        match = re.search(
            r"[0-9]*\.[0-9]*\.[0-9]*",
            matchline.group(0),
        )

    if match:
        return [int(v) for v in match.group(0).split(".")]
    else:
        return None
