# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI Process helper module."""

from os import environ
from subprocess import PIPE, CalledProcessError
from subprocess import Popen as popen
from subprocess import run


class ProcessResponse():
    """Process response class."""

    def __init__(self, output=None, error=None, status_code=0, warning=False):
        """Constructor.

        By default it is a successful response (0) wiht no error nor ouput.
        """
        self.output = output
        self.error = error
        self.status_code = status_code
        self.warning = warning


def run_cmd(command):
    """Runs a given command and returns a ProcessResponse."""
    p = popen(command, stdout=PIPE, stderr=PIPE)
    output, error = p.communicate()
    output = output.decode("utf-8")
    error = error.decode("utf-8")

    return ProcessResponse(output, error, p.returncode)


def run_interactive(command, env=None, skippable=False):
    """Runs a given command without blocking, allows interactive shells.

    Stdout and stderr are not piped and therefore allows interaction.
    :param command: The command to run, in array form.
    :param env: A dict of variables to add to the environment.
    """
    full_env = environ.copy()  # Need to inherit the global one
    if env:
        for var, val in env.items():
            full_env[var] = val

    try:
        response = run(command, check=True, env=full_env)
        return ProcessResponse(
            output=None, error=None, status_code=0)
    except CalledProcessError as e:
        if skippable:
            return ProcessResponse(
                output=e.stdout, error=e.stderr, status_code=0, warning=True)
        else:
            return ProcessResponse(
                output=e.stdout, error=e.stderr, status_code=e.returncode)
