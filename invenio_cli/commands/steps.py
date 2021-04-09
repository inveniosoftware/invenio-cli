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

    Is composed of a function, arguments, and a message (feedback).
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

    Is composed of a command, an environment, and a message (feedback).
    """

    def __init__(self, cmd, env=None, message=None, skippable=False):
        """Constructor."""
        self.cmd = cmd
        self.env = env
        self.message = message
        self.skippable = skippable

    def execute(self):
        """Execute the function with the given arguments."""
        return run_interactive(self.cmd, self.env, self.skippable)
