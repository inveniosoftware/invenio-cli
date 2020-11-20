# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from ..helpers.process import run_interactive


class FunctionStep(object):
    """A step which execution is a function call.

    Is composed of message (feedback), a funcion, and arguments.
    """

    def __init__(self, func, args=None, message=None):
        """Constructor."""
        self.func = func
        self.args = args or {}
        self.message = message

    def execute(self):
        """Execute the function with the given arguments."""
        return self.func(**self.args)


class CommandStep(object):
    """A step which execution is a command run.

    Is composed of message (feedback) and a command.
    """

    def __init__(self, cmd, env=None, message=None):
        """Constructor."""
        self.cmd = cmd
        self.env = env
        self.message = message

    def execute(self):
        """Execute the function with the given arguments."""
        return run_interactive(self.cmd, self.env)
