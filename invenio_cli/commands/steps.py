# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from ..helpers.process import run_interactive


class Step(object):
    """Interface for step objects."""

    def __init__(self, message=None, skippable=False):
        """Constructor."""
        self.message = message
        self.skippable = skippable

    def execute(self):
        """Execute the step."""
        raise NotImplementedError


class FunctionStep(Step):
    """A step which execution is a function call.

    Is composed of a function, arguments, and a message (feedback).
    """

    def __init__(self, func, args=None, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)
        self.func = func
        self.args = args or {}

    def execute(self):
        """Execute the function with the given arguments."""
        response = self.func(**self.args)

        if response.status_code > 0 and self.skippable:
            response.warning = True
            response.status_code = 0

        return response


class CommandStep(Step):
    """A step which execution is a command run.

    Is composed of a command, an environment, and a message (feedback).
    """

    def __init__(self, cmd, env=None, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)
        self.cmd = cmd
        self.env = env

    def execute(self):
        """Execute the function with the given arguments."""
        return run_interactive(self.cmd, self.env, self.skippable)
