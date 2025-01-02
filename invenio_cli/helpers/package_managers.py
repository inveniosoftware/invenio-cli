# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 TU Wien.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Wrappers around various package managers to be used under the hood."""

import os
from abc import ABC
from pathlib import Path
from typing import Dict, List, Union

from pynpm import NPMPackage, PNPMPackage


class PythonPackageManager(ABC):
    """Interface for creating tool-specific Python package management commands."""

    name: str = None
    lock_file_name: str = None

    def run_command(self, *command: str) -> List[str]:
        """Generate command to run the given command in the managed environment."""
        raise NotImplementedError()

    def editable_dev_install(self, package: str) -> List[str]:
        """Install the local packages as editable, but ignore it for locking."""
        raise NotImplementedError()

    def install_package(self, package: str, version: str = None) -> List[str]:
        """Install the package in the specified version."""
        raise NotImplementedError()

    def update_packages(self) -> List[str]:
        """Update all updated packages."""
        raise NotImplementedError()

    def list_outdated_packages(self) -> List[str]:
        """List outdated installed packages."""
        raise NotImplementedError()

    def install_locked_deps(self, prereleases: bool, devtools: bool) -> List[str]:
        """Install the packages according to the lock file."""
        raise NotImplementedError()

    def lock_dependencies(self, prereleases: bool, devtools: bool) -> List[str]:
        """Update the lock file."""
        raise NotImplementedError()

    def remove_venv(self) -> List[str]:
        """Remove the created virtualenv."""
        raise NotImplementedError()

    def start_activated_subshell(self) -> List[str]:
        """Remove the created virtualenv."""
        raise NotImplementedError()


class Pipenv(PythonPackageManager):
    """Generate ``pipenv`` commands for managing Python packages."""

    name = "pipenv"
    lock_file_name = "Pipfile.lock"

    def run_command(self, *command):
        """Generate command to run the given command in the managed environment."""
        return [self.name, "run", *command]

    def editable_dev_install(self, *packages):
        """Install the local packages as editable, but ignore it for locking."""
        cmd = [self.name, "run", "pip", "install"]
        for package in packages:
            cmd += ["-e", package]
        return cmd

    def install_package(self, package, version=None):
        """Install the package in the specified version."""
        package_version = package if not version else package + version
        return [self.name, "install", package_version]

    def update_packages(self):
        """Update all updated packages."""
        return [self.name, "update"]

    def list_outdated_packages(self):
        """List outdated installed packages."""
        return [self.name, "update", "--outdated"]

    def install_locked_deps(self, prereleases, devtools):
        """Install the packages according to the lock file."""
        cmd = [self.name, "sync"]
        if prereleases:
            cmd += ["--pre"]
        if devtools:
            cmd += ["--dev"]
        return cmd

    def lock_dependencies(self, prereleases, devtools):
        """Update the lock file."""
        cmd = [self.name, "lock"]
        if prereleases:
            cmd += ["--pre"]
        if devtools:
            cmd += ["--dev"]
        return cmd

    def remove_venv(self):
        """Remove the created virtualenv."""
        return ["pipenv", "--rm"]

    def start_activated_subshell(self) -> List[str]:
        """Remove the created virtualenv."""
        return ["pipenv", "shell"]


class UV(PythonPackageManager):
    """Generate ``uv`` commands for managing Python packages."""

    name = "uv"
    lock_file_name = "uv.lock"

    def run_command(self, *command):
        """Generate command to run the given command in the managed environment."""
        # "--no-sync" is used to not override locally installed editable packages
        return [self.name, "run", "--no-sync", *command]

    def editable_dev_install(self, *packages):
        """Install the local packages as editable, but ignore it for locking."""
        cmd = [self.name, "pip", "install"]
        for package in packages:
            cmd += ["-e", package]
        return cmd

    def install_package(self, package, version=None):
        """Install the package in the specified version."""
        package_version = package if not version else package + version
        return [self.name, "add", package_version]

    def update_packages(self):
        """Update all updated packages."""
        return [self.name, "sync", "--upgrade"]

    def list_outdated_packages(self):
        """List outdated installed packages."""
        return [self.name, "sync", "--upgrade", "--dry-run"]

    def install_locked_deps(self, prereleases, devtools):
        """Install the packages according to the lock file."""
        cmd = [self.name, "sync"]
        if prereleases:
            cmd += ["--prerelease", "allow"]
        if not devtools:
            cmd += ["--no-dev"]
        return cmd

    def lock_dependencies(self, prereleases, devtools):
        """Update the lock file."""
        cmd = [self.name, "lock"]
        if prereleases:
            cmd += ["--prerelease", "allow"]
        return cmd

    def remove_venv(self):
        """Remove the created virtualenv."""
        # This assumes the default location for the uv venv
        return ["rm", "-r", ".venv"]

    def start_activated_subshell(self) -> List[str]:
        """Remove the created virtualenv."""
        # This assumes we're using a Unixoid OS...
        # Since Invenio doesn't support Windows that should be given
        # Also, it has a good chance of not properly setting a PS1...
        shell = os.getenv("SHELL")
        return [shell, "-c", f"source .venv/bin/activate; exec {shell} -i"]


class JavascriptPackageManager(ABC):
    """Interface for creating tool-specific JS package management commands."""

    name = None

    def create_pynpm_package(self, package_json_path: Union[Path, str]) -> NPMPackage:
        """Create a variant of ``NPMPackage`` with the path to ``package.json``."""
        raise NotImplementedError()

    def install_local_package(self, path: Union[Path, str]) -> List[str]:
        """Install the local JS package."""
        raise NotImplementedError()

    def env_overrides(self) -> Dict[str, str]:
        """Provide environment overrides for building Invenio assets."""
        return {}


class NPM(JavascriptPackageManager):
    """Generate ``npm`` commands for managing JS packages."""

    name = "npm"

    def create_pynpm_package(self, package_json_path):
        """Create an ``NPMPackage`` with the path to ``package.json``."""
        return NPMPackage(package_json_path)

    def install_local_package(self, path):
        """Install the local JS package."""
        return ["--prefix", str(path)]

    def env_overrides(self):
        """Provide environment overrides for building Invenio assets."""
        return {"INVENIO_WEBPACKEXT_NPM_PKG_CLS": "pynpm:NPMPackage"}


class PNPM(JavascriptPackageManager):
    """Generate ``pnpm`` commands for managing JS packages."""

    name = "pnpm"

    def create_pynpm_package(self, package_json_path):
        """Create a ``PNPMPackage`` with the path to ``package.json``."""
        return PNPMPackage(package_json_path)

    def install_local_package(self, path):
        """Install the local JS package."""
        return ["-C", str(path)]

    def env_overrides(self):
        """Provide environment overrides for building Invenio assets."""
        return {"INVENIO_WEBPACKEXT_NPM_PKG_CLS": "pynpm:PNPMPackage"}
