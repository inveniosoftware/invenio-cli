# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2022-2025 Graz University of Technology.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import sys
from os import listdir

from ..helpers.process import ProcessResponse
from .steps import CommandStep


class PackagesCommands:
    """Local installation commands."""

    def __init__(self, cli_config):
        """Construct PackagesCommands."""
        self.cli_config = cli_config

    def install_packages(self, packages, log_file=None):
        """Steps to install Python packages.

        It is a class method since it does not require any configuration.
        """
        if self.cli_config.python_packages_manager == "uv":
            cmd = ["uv", "pip", "install"]
        elif self.cli_config.python_packages_manager == "pip":
            cmd = ["pipenv", "run", "pip", "install"]
        else:
            print("please configure python package manager.")
            sys.exit()

        for package in packages:
            cmd.extend(["-e", package])

        steps = [
            CommandStep(
                cmd=cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Installing python dependencies...",
                log_file=log_file,
            )
        ]

        return steps

    def outdated_packages(self):
        """Steps to show outdated packages.

        It is a class method since it does not require any configuration.
        """
        if self.cli_config.python_packages_manager == "uv":
            raise RuntimeError("not yet ported to uv")
        elif self.cli_config.python_packages_manager == "pip":
            cmd = ["pipenv", "update", "--outdated"]
        else:
            print("please configure python package manager.")
            sys.exit()

        steps = [
            CommandStep(
                cmd=cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Checking outdated packages...",
            )
        ]

        return steps

    def update_packages(self):
        """Steps to update all Python packages.

        It is a class method since it does not require any configuration.
        """
        if self.cli_config.python_packages_manager == "uv":
            cmd = ["uv", "sync", "--upgrade"]
        elif self.cli_config.python_packages_manager == "pip":
            cmd = ["pipenv", "update"]
        else:
            print("please configure python package manager.")
            sys.exit()

        steps = [
            CommandStep(
                cmd=cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Updating package(s)...",
            )
        ]

        return steps

    def update_package_new_version(self, package, version):
        """Update invenio-app-rdm version.

        It is a class method since it does not require any configuration.
        """
        if self.cli_config.python_packages_manager == "uv":
            raise RuntimeError("not yet ported to uv")
        elif self.cli_config.python_packages_manager == "pip":
            cmd = ["pipenv", "install", package + version]
        else:
            print("please configure python package manager.")
            sys.exit()

        steps = [
            CommandStep(
                cmd=cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message=f"Updating {package} to version {version}...",
            )
        ]

        return steps

    def install_locked_dependencies(self, pre, dev):
        """Install dependencies from requirements.txt using install."""
        if self.cli_config.python_packages_manager == "uv":
            cmd = ["uv", "sync"]
        elif self.cli_config.python_packages_manager == "pip":
            cmd = ["pipenv", "sync"]
            if pre:
                cmd += ["--pre"]
            if dev:
                cmd += ["--dev"]
        else:
            print("please configure python package manager.")
            sys.exit()

        steps = [
            CommandStep(
                cmd=cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Installing python dependencies... Please be "
                + "patient, this operation might take some time...",
            )
        ]

        return steps

    def lock(self, pre, dev):
        """Steps to lock Python dependencies."""
        if self.cli_config.python_packages_manager == "uv":
            cmd = ["uv", "lock"]
        elif self.cli_config.python_packages_manager == "pip":
            cmd = ["pipenv", "lock"]
            if pre:
                cmd += ["--pre"]
            if dev:
                cmd += ["--dev"]
        else:
            print("please configure python package manager.")
            sys.exit()

        steps = [
            CommandStep(
                cmd=cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Locking python dependencies...",
            )
        ]

        return steps

    def is_locked(self):
        """Checks if the dependencies have been locked."""
        if self.cli_config.python_packages_manager == "uv":
            locked = "uv.lock" in listdir(".")
        elif self.cli_config.python_packages_manager == "pip":
            locked = "Pipfile.lock" in listdir(".")
        else:
            print("please configure python package manager.")
            sys.exit()

        if not locked:
            return ProcessResponse(
                error="Dependencies were not locked. "
                + "Please run `invenio-cli packages lock`.",
                status_code=1,
            )

        return ProcessResponse(
            output="Dependencies are locked",
            status_code=0,
        )
