# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import click

from ..commands import InstallCommands
from .utils import pass_cli_config, run_steps


@click.group(invoke_without_command=True)
@click.pass_context
def install(ctx):
    """Commands for installing the project."""
    if ctx.invoked_subcommand is None:
        # If no sub-command is passed, default to the install all command.
        ctx.invoke(install_all)


@install.command("all")
@click.option(
    "--pre",
    default=False,
    is_flag=True,
    help="If specified, allows the installation of alpha releases",
)
@click.option(
    "--dev/--no-dev",
    default=True,
    is_flag=True,
    help="Includes development dependencies.",
)
@click.option(
    "--production/--development",
    "-p/-d",
    default=False,
    is_flag=True,
    help="Production mode copies statics/assets. Development mode symlinks"
    " statics/assets.",
)
@pass_cli_config
def install_all(cli_config, pre, dev, production):
    """Installs the project locally.

    Installs dependencies, creates instance directory,
    links invenio.cfg + templates, copies images and other statics and finally
    builds front-end assets.
    """
    commands = InstallCommands(cli_config)
    steps = commands.install(
        pre=pre,
        dev=dev,
        debug=not production,
    )
    on_fail = "Failed to install dependencies."
    on_success = "Dependencies installed successfully."

    run_steps(steps, on_fail, on_success)


@install.command()
@pass_cli_config
def symlink(cli_config):
    """Symlinks project files in the instance directory."""
    commands = InstallCommands(cli_config)
    steps = commands.symlink()
    on_fail = "Failed to symlink project files and folders."
    on_success = "Project ffles and folders symlinked successfully."

    run_steps(steps, on_fail, on_success)
