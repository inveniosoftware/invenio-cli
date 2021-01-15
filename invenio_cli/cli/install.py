# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import click

from ..commands import InstallCommands
from ..helpers.cli_config import CLIConfig
from .utils import pass_cli_config, run_steps


@click.command()
@click.option('--pre', default=False, is_flag=True,
              help='If specified, allows the installation of alpha releases')
@click.option('--dev/--no-dev', default=True, is_flag=True,
              help='Includes development dependencies.')
@click.option(
    '--production/--development', '-p/-d', default=False, is_flag=True,
    help='Production mode copies statics/assets. Development mode symlinks'
         ' statics/assets.'
)
@pass_cli_config
def install(cli_config, pre, dev, production):
    """Installs the  project locally.

    Installs dependencies, creates instance directory,
    links invenio.cfg + templates, copies images and other statics and finally
    builds front-end assets.
    """
    commands = InstallCommands(cli_config)
    flask_env = 'production' if production else 'development'
    steps = commands.install(pre=pre, dev=dev, flask_env=flask_env)
    on_fail = "Failed to install dependencies."
    on_success = "Dependencies installed successfully."

    run_steps(steps, on_fail, on_success)
