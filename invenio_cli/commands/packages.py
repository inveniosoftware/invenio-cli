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

from ..helpers.cli_config import CLIConfig
from ..helpers.process import ProcessResponse
from .steps import CommandStep


class PackagesCommands(object):
    """Local installation commands."""

    def __init__(self, cli_config: CLIConfig):
        """Construct PackagesCommands."""
        self.cli_config = cli_config

    def install_packages(self, packages, log_file=None):
        """Steps to install Python packages."""
        cmd = self.cli_config.python_packages_manager.editable_dev_install(*packages)
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
        """Steps to show outdated packages."""
        cmd = self.cli_config.python_packages_manager.list_outdated_packages()
        steps = [
            CommandStep(
                cmd=cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Checking outdated packages...",
            )
        ]

        return steps

    def update_packages(self):
        """Steps to update all Python packages."""
        cmd = self.cli_config.python_packages_manager.update_packages()
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
        cmd = self.cli_config.python_packages_manager.install_package(package, version)
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
        cmd = self.cli_config.python_packages_manager.install_locked_deps(pre, dev)
        steps = [
            CommandStep(
                cmd=cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message=(
                    "Installing python dependencies... Please be patient, this operation might take some time..."
                ),
            )
        ]

        return steps

    def lock(self, pre, dev):
        """Steps to lock Python dependencies."""
        cmd = self.cli_config.python_packages_manager.lock_dependencies(pre, dev)
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
        lock_file_name = self.cli_config.python_packages_manager.lock_file_name
        locked = lock_file_name in listdir(".")

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
