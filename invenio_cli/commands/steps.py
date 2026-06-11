# SPDX-FileCopyrightText: 2020-2021 CERN.
# SPDX-FileCopyrightText: 2022 Graz University of Technology.
# SPDX-License-Identifier: MIT

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

    def __init__(self, cmd, env=None, log_file=None, **kwargs):
        """Constructor."""
        super().__init__(**kwargs)
        self.cmd = cmd
        self.env = env
        self.log_file = log_file

    def execute(self):
        """Execute the command, an op (RPCOp/LocalOp) or a plain argv list."""
        if callable(self.cmd):
            response = self.cmd(env=self.env, log_file=self.log_file)
            if response.status_code > 0 and self.skippable:
                response.warning = True
                response.status_code = 0
            return response
        return run_interactive(self.cmd, self.env, self.skippable, self.log_file)
