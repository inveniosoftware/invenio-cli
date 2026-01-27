# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from ..helpers.cli_config import CLIConfig
from ..helpers.env import env
from ..helpers.process import run_interactive
from .steps import CommandStep


class Commands(object):
    """Abstraction over CLI commands that are either local or containerized."""

    def __init__(self, cli_config: CLIConfig):
        """Constructor.

        :param cli_config: :class:CLIConfig instance
        """
        self.cli_config = cli_config

    def shell(self):
        """Start a shell in the virtual environment."""
        command = self.cli_config.python_package_manager.start_activated_subshell()
        return run_interactive(command, env={"PIPENV_VERBOSITY": "-1"})

    def pyshell(self, debug=False):
        """Start a Python shell."""
        pkg_man = self.cli_config.python_package_manager
        with env(FLASK_DEBUG="1" if debug else "0"):
            command = pkg_man.run_command("invenio", "shell")
            return run_interactive(command, env={"PIPENV_VERBOSITY": "-1"})

    def destroy(self):
        """Destroys the instance's virtualenv.

        NOTE: This function has no knowledge of the existence of services.
              Refer to services.py to destroy services' containers.
        """
        command = self.cli_config.python_package_manager.remove_venv()
        steps = [
            CommandStep(
                cmd=command,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Destroying virtual environment",
            )
        ]

        return steps
