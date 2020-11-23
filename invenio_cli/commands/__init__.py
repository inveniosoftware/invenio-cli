# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""


from .commands import Commands
from .containers import ContainersCommands
from .local import AssetsCommands, InstallCommands, LocalCommands, \
    ServicesCommands

__all__ = (
    "Commands",
    "ContainersCommands",
    "AssetsCommands",
    "LocalCommands",
    "InstallCommands",
    "ServicesCommands",
)
