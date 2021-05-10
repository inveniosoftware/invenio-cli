# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from os import listdir

from ..helpers.process import ProcessResponse
from .steps import CommandStep


class PackagesCommands(object):
    """Local installation commands."""

    @staticmethod
    def install_packages(packages):
        """Steps to install Python packages.

        It is a class method since it does not require any configuration.
        """
        prefix = ['pipenv', 'run']
        cmd = prefix + ['pip', 'install']
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

    @staticmethod
    def outdated_packages():
        """Steps to show outdated packages.

        It is a class method since it does not require any configuration.
        """
        cmd = ['pipenv', 'update', '--outdated']

        steps = [
            CommandStep(
                cmd=cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message="Checking outdated packages..."
            )
        ]

        return steps

    @staticmethod
    def update_packages():
        """Steps to update all Python packages.

        It is a class method since it does not require any configuration.
        """
        cmd = ['pipenv', 'update']

        steps = [
            CommandStep(
                cmd=cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message="Updating package(s)..."
            )
        ]

        return steps

    @staticmethod
    def update_package_new_version(package, version):
        """Update invenio-app-rdm version.

        It is a class method since it does not require any configuration.
        """
        prefix = ['pipenv']
        app = prefix + ['install', package + version]

        steps = [
            CommandStep(
                cmd=app,
                env={'PIPENV_VERBOSITY': "-1"},
                message=f"Updating {package} to version {version}..."
            )
        ]

        return steps

    @staticmethod
    def install_locked_dependencies(pre):
        """Installed dependencies from Pipfile.lock using sync."""
        # NOTE: sync has not interactive process feedback
        cmd = ['pipenv', 'sync']
        if pre:
            cmd += ['--pre']

        steps = [
            CommandStep(
                cmd=cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message="Installing python dependencies... Please be " +
                        "patient, this operation might take some time..."
            )
        ]

        return steps

    @staticmethod
    def lock(pre, dev):
        """Steps lock Python dependencies."""
        cmd = ['pipenv', 'lock']
        if pre:
            cmd += ['--pre']
        if dev:
            cmd += ['--dev']

        steps = [
            CommandStep(
                cmd=cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message="Locking python dependencies..."
            )
        ]

        return steps

    @staticmethod
    def is_locked():
        """Checks if the dependencies have been locked."""
        locked = 'Pipfile.lock' in listdir('.')
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
