# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""


from pathlib import Path

from pynpm import NPMPackage
import click

from ...helpers import env
from ...helpers.process import run_interactive
from .local import LocalCommands


class AssetsCommands(LocalCommands):
    """Local installation commands."""

    def __init__(self, cli_config):
        """Constructor."""
        super(AssetsCommands, self).__init__(cli_config)

    def watch_assets(self):
        """High-level command to watch assets for changes."""
        # Commands
        prefix = ['pipenv', 'run']
        watch_cmd = prefix + ['invenio', 'webpack', 'run', 'start']

        with env(FLASK_ENV='development'):
            # Collect into statics/ and assets/ folder
            click.secho('Starting assets watching (press CTRL+C to stop)...',
                        fg='green')
            run_interactive(watch_cmd, check=True)

    @staticmethod
    def _watch_js_module(pkg):
        """Watch the JS module for changes."""
        click.secho('Starting watching module...', fg='green')
        pkg.run_script('watch')

    @staticmethod
    def _module_pkg(path):
        """NPM package for the given path."""
        return NPMPackage(Path(path) / 'package.json')

    def _assets_pkg(self):
        """NPM package for the instance's webpack project."""
        return self._module_pkg(self.cli_config.get_instance_path() / 'assets')

    def link_js_module(self, path):
        """High-level command to install and build a JS module."""
        module_pkg = self._module_pkg(path)
        assets_pkg = self._assets_pkg()

        # Create link to global folder
        click.secho('Linking module...', fg='green')
        module_pkg.run_script('link-dist')

        # Link the global folder to the assets folder.
        assets_pkg.link(module_pkg.package_json['name'])

    def watch_js_module(self, path, link=True):
        """High-level command to watch a JS module for changes."""
        if link:
            self.link_js_module(path)

        click.secho('Starting watching module...', fg='green')
        self._module_pkg(path).run_script('watch')
