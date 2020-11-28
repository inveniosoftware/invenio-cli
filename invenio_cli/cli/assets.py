# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import click
from click_default_group import DefaultGroup

from ..commands import AssetsCommands
from .utils import pass_cli_config, run_steps


@click.group()
def assets():
    """Statics and assets management commands.

    NOTE: The assets commands are intended for development environments.
          To re-build assets on a containers environment use
          `invenio-cli containers build`.
    """


@assets.command()
@click.option('--no-wipe', '-n', default=False, is_flag=True,
              help='Do not remove existing assets.')
@click.option(
    '--production/--development', '-p/-d', default=False, is_flag=True,
    help='Production mode copies files. Development mode symlinks files.'
)
@pass_cli_config
def build(cli_config, no_wipe, production):
    """Build the static and assets files on the local installation."""
    commands = AssetsCommands(cli_config)
    commands.update_statics_and_assets(
        force=not no_wipe,  # If no_wipe=True, it means force=False
        flask_env='production' if production else 'development'
    )


@assets.command()
@click.argument('path', type=click.Path(exists=True))
@pass_cli_config
def install(cli_config, path):
    """Install and link a React module on the local installation."""
    commands = AssetsCommands(cli_config)

    click.secho("Installing React module...", fg="green")
    steps = commands.link_js_module(path)
    on_fail = "Failed to install React module."
    on_success = "React module installed successfully."

    run_steps(steps, on_fail, on_success)


@assets.command('watch')
@pass_cli_config
def watch_assets(cli_config):
    """Watch assets files on the local installation.

    This is the default behaviour when calling `invenio-cli assets watch`.
    """
    commands = AssetsCommands(cli_config)
    commands.watch_assets()


@assets.command('watch-module')
@click.option('--link', '-l', default=False, is_flag=True,
              help='Link the module.')
@click.argument('path', type=click.Path(exists=True))
@pass_cli_config
def watch_module(cli_config, path, link):
    """Watch a React module on the local installation."""
    commands = AssetsCommands(cli_config)
    click.secho("Watching React module...", fg="green")
    steps = commands.watch_js_module(path, link=link)
    on_fail = "Failed set watcher on React module."
    on_success = "Finished watching React module."

    run_steps(steps, on_fail, on_success)
