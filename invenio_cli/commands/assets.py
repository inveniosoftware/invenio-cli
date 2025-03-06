# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from pathlib import Path

import click

from ..helpers import env
from ..helpers.process import ProcessResponse, run_interactive
from .local import LocalCommands
from .steps import FunctionStep


class AssetsCommands(LocalCommands):
    """Local installation commands."""

    def __init__(self, cli_config):
        """Constructor."""
        super().__init__(cli_config)

    def _module_pkg(self, path):
        """NPM package for the given path."""
        path = Path(path) / "package.json"
        return self.cli_config.javascript_package_manager.create_pynpm_package(path)

    def _assets_pkg(self):
        """NPM package for the instance's webpack project."""
        return self._module_pkg(self.cli_config.get_instance_path() / "assets")

    def _watch_js_module(self, pkg):
        """Watch the JS module for changes."""
        click.secho("Starting watching module...", fg="green")
        status_code = pkg.run_script("watch")
        if status_code == 0:
            return ProcessResponse(output="Watched module successfully.", status_code=0)
        else:
            return ProcessResponse(
                error=f"Unable to set watcher. Got status code {status_code}",
                status_code=status_code,
            )

    def _npm_install_command(self, path, module_pkg):
        """Run command and return a ProcessResponse."""
        install_args = self.cli_config.javascript_package_manager.install_local_package(
            path
        )
        status_code = module_pkg.install(" ".join(install_args))
        if status_code == 0:
            return ProcessResponse(
                output="Dependent packages installed correctly", status_code=0
            )
        else:
            return ProcessResponse(
                error="Unable to install dependent packages. "
                "Got error code {status_code}",
                status_code=status_code,
            )

    @staticmethod
    def _build_script(module_pkg):
        """Run script and return a ProcessResponse."""
        status_code = module_pkg.run_script("build")
        if status_code == 0:
            return ProcessResponse(output="Built correctly", status_code=0)
        else:
            return ProcessResponse(
                error=f"Unable to build. Got error code {status_code}",
                status_code=status_code,
            )

    def watch_assets(self):
        """High-level command to watch assets for changes."""
        watch_cmd = self.cli_config.python_package_manager.run_command(
            "invenio",
            "webpack",
            "run",
            "start",
        )

        with env(FLASK_DEBUG="1"):
            # Collect into statics/ and assets/ folder
            click.secho(
                "Starting assets watching (press CTRL+C to stop)...", fg="green"
            )
            run_interactive(watch_cmd, env={"PIPENV_VERBOSITY": "-1"})

    def link_js_module(self, path):
        """High-level command to install and build a JS module."""
        module_pkg = self._module_pkg(path)
        assets_pkg = self._assets_pkg()

        steps = [
            FunctionStep(  # Install dependent packages
                func=self._npm_install_command,
                args={"path": path, "module_pkg": module_pkg},
                message="Installing dependent packages...",
            ),
            FunctionStep(  # Run build script
                func=self._build_script,
                args={"module_pkg": module_pkg},
                message="Building...",
            ),
        ]

        # The commands necessary for linking local JS packages vary by package manager
        js_package_manager = self.cli_config.javascript_package_manager
        link_steps = [
            FunctionStep(
                func=step.function,
                args={"assets_pkg": assets_pkg, "module_pkg": module_pkg},
                message=step.message,
            )
            for step in js_package_manager.package_linking_steps()
        ]
        steps.extend(link_steps)

        return steps

    def watch_js_module(self, path, link=True):
        """High-level command to watch a JS module for changes."""
        steps = []
        if link:
            steps.extend(self.link_js_module(path))

        steps.append(
            FunctionStep(
                func=self._watch_js_module,
                args={"pkg": self._module_pkg(path)},
                message="Starting watching module...",
            )
        )

        return steps
