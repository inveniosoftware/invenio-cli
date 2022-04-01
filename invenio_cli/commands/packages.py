# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from os import listdir

from ..helpers.packaging import get_packaging_backend
from ..helpers.process import ProcessResponse
from .commands import Commands
from .steps import CommandStep


class PackagesCommands(Commands):
    """Local installation commands."""

    def install_packages(self, packages):
        """Steps to install Python packages."""
        cmd = get_packaging_backend(self.cli_config).run_command(
            "pip", "install"
        )
        for package in packages:
            cmd.extend(['-e', package])

        steps = [
            CommandStep(
                cmd=cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message="Installing python dependencies..."
            )
        ]

        return steps

    def outdated_packages(self):
        """Steps to show outdated packages."""
        pkg_backend = get_packaging_backend(self.cli_config)
        cmd = pkg_backend.outdated_packages_command()

        steps = [
            CommandStep(
                cmd=cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message="Checking outdated packages..."
            )
        ]

        return steps

    def update_packages(self):
        """Steps to update all Python packages."""
        cmd = get_packaging_backend(self.cli_config).update_command()

        steps = [
            CommandStep(
                cmd=cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message="Updating package(s)..."
            )
        ]

        return steps

    def update_package_new_version(self, package, version):
        """Update invenio-app-rdm version."""
        pkg = package + version
        cmd = get_packaging_backend(self.cli_config).add_package_command(pkg)

        steps = [
            CommandStep(
                cmd=cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message=f"Updating {package} to version {version}..."
            )
        ]

        return steps

    def install_locked_dependencies(self, pre, dev):
        """Install dependencies from Pipfile.lock using sync."""
        # NOTE: sync has no interactive process feedback
        # TODO: check if the `pre` flag makes sense here
        pkg_backend = get_packaging_backend(self.cli_config)
        cmd = pkg_backend.install_dependencies_command(dev)

        steps = [
            CommandStep(
                cmd=cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message="Installing python dependencies... Please be " +
                        "patient, this operation might take some time..."
            )
        ]

        return steps

    def lock(self, pre, dev):
        """Steps to lock Python dependencies."""
        # TODO check the `pre` flag with poetry
        pkg_backend = get_packaging_backend(self.cli_config)
        cmd = pkg_backend.lock_dependencies_command(dev, pre)

        steps = [
            CommandStep(
                cmd=cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message="Locking python dependencies..."
            )
        ]

        return steps

    def is_locked(self):
        """Checks if the dependencies have been locked."""
        pkg_backend = get_packaging_backend(self.cli_config)
        lock_file_name = pkg_backend.lock_file_name
        locked = lock_file_name in listdir('.')

        if not locked:
            return ProcessResponse(
                error="Dependencies were not locked. " +
                      "Please run `invenio-cli packages lock`.",
                status_code=1,
            )

        return ProcessResponse(
            output="Dependencies are locked",
            status_code=0,
        )
