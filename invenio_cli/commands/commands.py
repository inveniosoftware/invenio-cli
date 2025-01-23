# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2024-2025 Graz University of Technology.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import os
import sys
from pathlib import Path

from ..helpers.env import env
from ..helpers.process import run_interactive
from .steps import CommandStep


def reload_editable_package(item):
    """Reload editable packages.

    Manually process a .pth file to add paths to sys.path or execute import
    statements. Only necessary on the install step, because assets build doesn't
    know the previously install packages
    """
    with Path(item).open("r") as pth_file:
        for line in pth_file:
            line = line.strip()

            if line.startswith("import"):
                exec(line)
            elif os.path.isdir(line) and line not in sys.path:
                sys.path.insert(0, line)


class Commands:
    """Abstraction over CLI commands that are either local or containerized."""

    def __init__(self, cli_config):
        """Constructor.

        :param cli_config: :class:CLIConfig instance
        """
        self.cli_config = cli_config

        if "VIRTUAL_ENV" in os.environ:
            site_package = os.path.join(
                os.environ.get("VIRTUAL_ENV"),
                "lib",
                f"python{sys.version_info.major}.{sys.version_info.minor}",
                "site-packages",
            )
            sys.path.insert(0, site_package)

            for item in os.listdir(site_package):
                if item.startswith("__editable__") and item.endswith(".pth"):
                    reload_editable_package(site_package + "/" + item)

    @classmethod
    def shell(cls):
        """Start a shell in the virtual environment."""
        command = [
            "pipenv",
            "shell",
        ]
        return run_interactive(command, env={"PIPENV_VERBOSITY": "-1"})

    @classmethod
    def pyshell(cls, debug=False):
        """Start a Python shell."""
        with env(FLASK_ENV="development" if debug else "production"):
            command = ["pipenv", "run", "invenio", "shell"]
            return run_interactive(command, env={"PIPENV_VERBOSITY": "-1"})

    def destroy(self):
        """Destroys the instance's virtualenv.

        NOTE: This function has no knowledge of the existence of services.
              Refer to services.py to destroy services' containers.
        """
        steps = [
            CommandStep(
                cmd=["pipenv", "--rm"],
                env={"PIPENV_VERBOSITY": "-1"},
                message="Destroying virtual environment",
            )
        ]

        return steps
