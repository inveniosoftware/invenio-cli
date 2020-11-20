# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""


class InvenioCLIConfigError(Exception):
    """Exception when reading/writting from the configuration file."""

    def __init__(self, message):
        """Constructor."""
        super().__init__()
        self.message = message
