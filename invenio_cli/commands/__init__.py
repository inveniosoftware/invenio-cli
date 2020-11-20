# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from .assets import AssetsCommands
from .commands import Commands
from .containers import ContainersCommands
from .install import InstallCommands
from .local import LocalCommands
from .packages import PackagesCommands
from .services import ServicesCommands

__all__ = (
    "AssetsCommands",
    "Commands",
    "ContainersCommands",
    "InstallCommands",
    "LocalCommands",
    "PackagesCommands",
    "ServicesCommands",
)
