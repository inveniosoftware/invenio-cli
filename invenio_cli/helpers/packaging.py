# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2022 TU Wien.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Wrappers for packaging tools."""

from abc import ABC, abstractmethod


class PackagingBackend(ABC):
    """Base wrapper for packaging tools."""

    bin_name = None

    def run_command(self, *args):
        """Get the command for running a command inside the venv."""
        return [self.bin_name, "run", *args]

    def shell_command(self):
        """Get the command for activating the venv."""
        return [self.bin_name, "shell"]

    def update_command(self):
        """Get the command for updating the locked packages."""
        return [self.bin_name, "update"]

    @abstractmethod
    def outdated_packages_command(self):
        """Get the command to look up outdated packages."""
        raise NotImplementedError()

    @abstractmethod
    def add_package_command(self, *args, pre_release=False):
        """Get the command for installing a new package."""
        raise NotImplementedError()

    @abstractmethod
    def lock_dependencies_command(self, dev_packages, pre_releases):
        """Get the command for locking the packages."""
        raise NotImplementedError()

    @abstractmethod
    def install_dependencies_command(self, dev_packages):
        """Get the command for installing the locked packages."""
        raise NotImplementedError()

    @abstractmethod
    def remove_venv_command(self):
        """Get the command for removing the created venv."""
        raise NotImplementedError()

    @property
    @abstractmethod
    def lock_file_name(self):
        """Get the name of the lock file."""
        raise NotImplementedError()


class PipenvBackend(PackagingBackend):
    """Pipenv packaging backend."""

    bin_name = "pipenv"

    def outdated_packages_command(self):
        """Get the command to look up outdated packages."""
        return [self.bin_name, "update", "--outdated"]

    def add_package_command(self, *args, pre_release=False):
        """Get the command for installing a new package."""
        cmd = [self.bin_name, "install"]
        if pre_release:
            cmd += ["--pre"]

        return [*cmd, *args]

    def lock_dependencies_command(self, dev_packages, pre_releases):
        """Get the command for locking the packages."""
        cmd = [self.bin_name, "lock"]
        if dev_packages:
            cmd += ["--dev"]
        if pre_releases:
            cmd += ["--pre"]

        return cmd

    def install_dependencies_command(self, dev_packages):
        """Get the command for installing the locked packages."""
        cmd = [self.bin_name, "install"]
        if dev_packages:
            cmd += ["--dev"]

        return cmd

    def remove_venv_command(self):
        """Get the command for removing the created venv."""
        return [self.bin_name, "--rm"]

    @property
    def lock_file_name(self):
        """Get the name of the lock file."""
        return "Pipfile.lock"


class PoetryBackend(PackagingBackend):
    """Poetry packaging backend."""

    bin_name = "poetry"

    def outdated_packages_command(self):
        """Get the command to look up outdated packages."""
        return [self.bin_name, "show", "--outdated"]

    def add_package_command(self, *args, pre_release=False):
        """Get the command for installing a new package."""
        cmd = [self.bin_name, "add"]
        if pre_release:
            cmd += ["--allow-prereleases"]

        return [*cmd, *args]

    def lock_dependencies_command(self, dev_packages, pre_releases):
        """Get the command for locking the packages."""
        # it seems that `poetry lock` doesn't accept `--dev` or `--pre` flags
        # TODO verify!
        return [self.bin_name, "lock"]

    def install_dependencies_command(self, dev_packages):
        """Get the command for installing the locked packages."""
        cmd = [self.bin_name, "install"]
        if not dev_packages:
            # NOTE: this is being deprecated in poetry 1.2.x
            cmd += ["--no-dev"]

        return cmd

    def remove_venv_command(self):
        """Get the command for removing the created venv."""
        return [self.bin_name, "env", "remove", "--all", "--quiet"]

    @property
    def lock_file_name(self):
        """Get the name of the lock file."""
        return "poetry.lock"


def get_packaging_backend(config):
    """Get the packaging backend specified in the given configuration.

    If no configuration is specified, or if it has an invalid value
    configured, the ``PipenvBackend`` will be returned as a fallback.
    """
    if config is not None:
        backend_name = config.get_packaging_backend()
        if backend_name.lower() == "poetry":
            return PoetryBackend()
        elif backend_name.lower() == "pipenv":
            return PipenvBackend()

    # the default value is pipenv, as that's been used so far
    return PipenvBackend()
