# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI Process helper module."""

from subprocess import PIPE
from subprocess import Popen as popen


class ProcessResponse():
    """Process response class."""

    def __init__(self, output, error, status_code):
        """Constructor."""
        self.output = output
        self.error = error
        self.status_code = status_code


def run_cmd(command):
    """Runs a given command and returns a ProcessResponse."""
    p = popen(command, stdout=PIPE, stderr=PIPE)
    output, error = p.communicate()
    output = output.decode("utf-8")
    error = error.decode("utf-8")

    return ProcessResponse(output, error, p.returncode)
