# -*- coding: utf-8 -*-
#
# Copyright (C) 2025 TU Wien.
# Copyright (C) 2025 Graz University of Technology.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Wrappers around various package managers to be used under the hood."""

import atexit
import os
from abc import ABC
from subprocess import Popen
from typing import List

from .process import run_cmd


class PythonPackageManager(ABC):
    """Interface for creating tool-specific Python package management commands."""

    name: str = None
    lock_file_name: str = None
    rpc_server_is_running: bool = False
    rpc_server: Popen = None
    run_prefix: List = []

    def __init__(self):
        """Construct."""
        self.rpc_server = Popen(
            self.run_prefix + ["invenio", "rpc-server", "start", "--port", "5001"]
        )
        atexit.register(self.cleanup)
        while True:
            response = run_cmd(
                self.run_prefix + ["rpc-server", "ping", "--port", "5001"]
            )
            if "pong" in response.output:
                self.rpc_server_is_running = True
                break

    def cleanup(self):
        """Cleanup."""
        if self.rpc_server:
            self.rpc_server.terminate()

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
    run_prefix = ["pipenv", "run"]

    def send_command(self, *command):
        """Send command to rpc server, default to run_command."""
        if self.rpc_server_is_running:
            # [1:] remove "invenio" from commands
            return [
                self.name,
                "run",
                "rpc-server",
                "send",
                "--port",
                "5001",
                "--plain",
                *command[1:],
            ]
        else:
            self.run_command(*command)

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
    run_prefix = ["uv", "run", "--no-sync"]

    def send_command(self, *command):
        """Send command to rpc server, default to run_command."""
        if self.rpc_server_is_running:
            # [1:] remove "invenio" from commands
            return [
                self.name,
                "run",
                "--no-sync",
                "rpc-server",
                "send",
                "--port",
                "5001",
                "--plain",
                *command[1:],
            ]
        else:
            return self.run_command(*command)

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
