# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI Process helper module."""

from subprocess import PIPE, run, CalledProcessError
from subprocess import Popen as popen


class ProcessResponse():
    """Process response class."""

    def __init__(self, output=None, error=None, status_code=0):
        """Constructor.

        By default it is a successful response (0) wiht no error nor ouput.
        """
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


def run_interactive(command):
    """Runs a given command without blocking, allows interactive shells.

    Stdout and stderr are not piped and therefore allows interaction.
    """
    try:
        response = run(command, check=True)
        return ProcessResponse(
            output=None, error=None, status_code=0)
    except CalledProcessError as e:
        return ProcessResponse(
            output=None, error=e.message, status_code=e.returncode)
