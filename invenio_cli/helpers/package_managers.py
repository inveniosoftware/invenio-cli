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
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from subprocess import Popen
from typing import Dict, List, Union

from pynpm import NPMPackage, PNPMPackage

from ..helpers.process import ProcessResponse
from .process import run_cmd


class PythonPackageManager(ABC):
    """Interface for creating tool-specific Python package management commands."""

    name: str = None
    lock_file_name: str = None
    rpc_server_is_running: bool = False
    rpc_server: Popen = None
    run_prefix: List = []

    def ensure_rpc_server_is_running(self):
        """Ensure rpc server is running."""
        if self.rpc_server_is_running:
            return

        # first check if a server is already running. so to use long running rpc server
        response = run_cmd(self.run_prefix + ["rpc-server", "ping", "--port", "5001"])
        if "pong" in response.output:
            self.rpc_server_is_running = True
            return

        # open if not
        self.rpc_server = Popen(
            self.run_prefix + ["invenio", "rpc-server", "start", "--port", "5001"]
        )

        atexit.register(self.cleanup)
        # check until the server is up and running
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
        self.ensure_rpc_server_is_running()

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
        self.ensure_rpc_server_is_running()

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


@dataclass
class AssetsFunction:
    """Function to run an assets command with `assets_pkg` and `module_pkg`."""

    function: Callable[[NPMPackage, NPMPackage], ProcessResponse]
    message: str


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

    def package_linking_steps(self) -> List[AssetsFunction]:
        """Generate steps to link the target package to the project."""
        raise NotImplementedError()


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

    def package_linking_steps(self):
        """Generate steps to link the target package to the project."""

        def _link_package_to_global(
            assets_pkg: NPMPackage, module_pkg: NPMPackage
        ) -> ProcessResponse:
            status_code = module_pkg.run_script("link-dist")
            if status_code == 0:
                return ProcessResponse(
                    output="Module linked correctly to global", status_code=0
                )
            else:
                return ProcessResponse(
                    error=f"Unable to link-dist. Got error code {status_code}",
                    status_code=status_code,
                )

        def _link_global_package(
            assets_pkg: NPMPackage, module_pkg: NPMPackage
        ) -> ProcessResponse:
            try:
                module_name = module_pkg.package_json["name"]
            except FileNotFoundError as e:
                return ProcessResponse(
                    error="No module found on the specified path. "
                    f"File not found {e.filename}",
                    status_code=1,
                )

            status_code = assets_pkg.link(module_name)
            if status_code == 0:
                return ProcessResponse(
                    output="Global module linked correctly to local folder",
                    status_code=0,
                )
            else:
                return ProcessResponse(
                    error=f"Unable to link module. Got error code {status_code}",
                    status_code=status_code,
                )

        return [
            AssetsFunction(_link_package_to_global, "Linking module to global dist..."),
            AssetsFunction(_link_global_package, "Linking module to assets..."),
        ]


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

    def package_linking_steps(self):
        """Generate steps to link the target package to the project."""

        def _prelink_dist(
            assets_pkg: NPMPackage, module_pkg: NPMPackage
        ) -> ProcessResponse:
            """Execute the "prelink-dist" script."""
            status_code = module_pkg.run_script("prelink-dist")
            if status_code == 0:
                return ProcessResponse(
                    output="Successfully ran prelink-dist script.",
                    status_code=0,
                )
            else:
                return ProcessResponse(
                    error=f"Unable to prelink-dist. Got error code {status_code}",
                    status_code=status_code,
                )

        def _link_package_single_step(
            assets_pkg: NPMPackage, module_pkg: NPMPackage
        ) -> ProcessResponse:
            """Execute the PNPM single-step package linking."""
            try:
                # Accessing `package_json` fails if the file can't be found
                module_pkg.package_json["name"]

                # This is geared towards Invenio JS packages...
                # But so are all the other steps
                status_code = assets_pkg.link(
                    str(module_pkg.package_json_path.parent / "dist")
                )
            except FileNotFoundError as e:
                return ProcessResponse(
                    error="No module found on the specified path. "
                    f"File not found {e.filename}",
                    status_code=1,
                )
            if status_code == 0:
                return ProcessResponse(
                    output="Module linked successfully to assets",
                    status_code=0,
                )
            else:
                return ProcessResponse(
                    error=f"Unable to link module. Got error code {status_code}",
                    status_code=status_code,
                )

        def _postlink_dist(
            assets_pkg: NPMPackage, module_pkg: NPMPackage
        ) -> ProcessResponse:
            """Execute the "postlink-dist" script."""
            status_code = module_pkg.run_script("postlink-dist")
            if status_code == 0:
                return ProcessResponse(
                    output="Successfully ran postlink-dist script.",
                    status_code=0,
                )
            else:
                return ProcessResponse(
                    error=f"Unable to run postlink-dist. Got error code {status_code}",
                    status_code=status_code,
                )

        return [
            AssetsFunction(_prelink_dist, "Executing prelink-dist script..."),
            AssetsFunction(_link_package_single_step, "Linking module to assets..."),
            AssetsFunction(_postlink_dist, "Executing postlink-dist script..."),
        ]
