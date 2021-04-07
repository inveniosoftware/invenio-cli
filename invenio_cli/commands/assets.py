# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""


import subprocess
from functools import partial
from pathlib import Path

import click
from pynpm import NPMPackage

from ..helpers import env
from ..helpers.process import ProcessResponse, run_interactive
from .local import LocalCommands
from .steps import CommandStep, FunctionStep


class AssetsCommands(LocalCommands):
    """Local installation commands."""

    def __init__(self, cli_config):
        """Constructor."""
        super(AssetsCommands, self).__init__(cli_config)

    @staticmethod
    def _module_pkg(path):
        """NPM package for the given path."""
        return NPMPackage(Path(path) / 'package.json')

    def _assets_pkg(self):
        """NPM package for the instance's webpack project."""
        return self._module_pkg(self.cli_config.get_instance_path() / 'assets')

    @staticmethod
    def _watch_js_module(pkg):
        """Watch the JS module for changes."""
        click.secho('Starting watching module...', fg='green')
        status_code = pkg.run_script('watch')
        if status_code == 0:
            return ProcessResponse(
                output="Watched module successfully.",
                status_code=0
            )
        else:
            return ProcessResponse(
                error=f"Unable to set watcher. Got status code {status_code}",
                status_code=status_code
            )

    @staticmethod
    def _run_script(module_pkg):
        """Run script and return a ProcessResponse."""
        status_code = module_pkg.run_script("link-dist")
        if status_code == 0:
            return ProcessResponse(
                output="Module linked correctly to global",
                status_code=0
            )
        else:
            return ProcessResponse(
                error=f"Unable to link-dist. Got error code {status_code}",
                status_code=status_code
            )

    @staticmethod
    def _npm_install_command(path):
        """Run command and return a ProcessResponse."""
        status_code = subprocess.call(["npm", "install", "--prefix", path])
        if status_code == 0:
            return ProcessResponse(
                output="Dependent packages installed correctly",
                status_code=0
            )
        else:
            return ProcessResponse(
                error=f"Unable to install dependent packages. "
                      "Got error code {status_code}",
                status_code=status_code
            )

    @staticmethod
    def _build_script(module_pkg):
        """Run script and return a ProcessResponse."""
        status_code = module_pkg.run_script("build")
        if status_code == 0:
            return ProcessResponse(
                output="Built correctly",
                status_code=0
            )
        else:
            return ProcessResponse(
                error=f"Unable to build. Got error code {status_code}",
                status_code=status_code
            )

    @staticmethod
    def _assets_link(assets_pkg, module_pkg):
        try:
            module_name = module_pkg.package_json['name']
        except FileNotFoundError as e:
            return ProcessResponse(
                error="No module found on the specified path. "
                      f"File not found {e.filename}",
                status_code=1
            )

        status_code = assets_pkg.link(module_name)
        if status_code == 0:
            return ProcessResponse(
                output="Global module linked correctly to local folder",
                status_code=0
            )
        else:
            return ProcessResponse(
                error=f"Unable to link module. Got error code {status_code}",
                status_code=status_code
            )

    def watch_assets(self):
        """High-level command to watch assets for changes."""
        # Commands
        prefix = ['pipenv', 'run']
        watch_cmd = prefix + ['invenio', 'webpack', 'run', 'start']

        with env(FLASK_ENV='development'):
            # Collect into statics/ and assets/ folder
            click.secho('Starting assets watching (press CTRL+C to stop)...',
                        fg='green')
            run_interactive(watch_cmd, env={'PIPENV_VERBOSITY': "-1"})

    def link_js_module(self, path):
        """High-level command to install and build a JS module."""
        module_pkg = self._module_pkg(path)
        assets_pkg = self._assets_pkg()

        steps = [
            FunctionStep(  # Install dependent packages
                func=self._npm_install_command,
                args={"path": path},
                message="Installing dependent packages..."
            ),
            FunctionStep(  # Run build script
                func=self._build_script,
                args={"module_pkg": module_pkg},
                message="Building..."
            ),
            FunctionStep(  # Create link to global folder
                func=self._run_script,
                args={"module_pkg": module_pkg},
                message="Linking module to global dist..."
            ),
            FunctionStep(  # Link the global folder to the assets folder.
                func=self._assets_link,
                args={
                    "assets_pkg": assets_pkg,
                    "module_pkg": module_pkg
                },
                message="Linking module to assets..."
            )
        ]

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
                message="Starting watching module..."
            )
        )

        return steps
