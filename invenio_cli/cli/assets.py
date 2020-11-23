# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import click

from ..commands import AssetsCommands
from ..helpers.cli_config import CLIConfig

# FIXME: This should be imported from cli.py
pass_cli_config = click.make_pass_decorator(CLIConfig, ensure=True)


@click.group()
def assets():
    """Statics and assets management commands."""


@assets.command()
@click.option('--force', '-f', default=False, is_flag=True,
              help='Force the full recreation the assets and statics.')
@click.option(
    '--production/--development', '-p/-d', default=True, is_flag=True,
    help='Production mode copies files. Development mode symlinks files.'
)
@pass_cli_config
def update(cli_config, force, production):
    """Updates the current application static/assets files."""
    commands = AssetsCommands(cli_config)
    commands.update_statics_and_assets(
        force=force,
        flask_env='production' if production else 'development'
    )


@assets.command('watch-assets')
@pass_cli_config
def watch_assets(cli_config):
    """Watch assets files for changes and rebuild."""
    commands = AssetsCommands(cli_config)
    commands.watch_assets()


@assets.command()
@click.argument('path', type=click.Path(exists=True))
@pass_cli_config
def install(cli_config, path):
    """Install and link a React module."""
    commands = AssetsCommands(cli_config)
    commands.link_js_module(path)


@assets.command('watch-module')
@click.option('--link', '-l', default=False, is_flag=True,
              help='Link the module.')
@click.argument('path', type=click.Path(exists=True))
@pass_cli_config
def watch_module(cli_config, path, link):
    """Watch a React module."""
    commands = AssetsCommands(cli_config)
    commands.watch_js_module(path, link=link)
