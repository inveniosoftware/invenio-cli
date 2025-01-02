# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2025 Graz University of Technology.
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
    flask_env = "production" if production else "development"
    steps = commands.install(pre=pre, dev=dev, flask_env=flask_env, re_lock=False)
    on_fail = "Failed to install dependencies."
    on_success = "Dependencies installed successfully."

    run_steps(steps, on_fail, on_success)


@install.command("python")
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
@pass_cli_config
def install_python(cli_config, pre, dev):
    """Install Python dependencies and packages."""
    commands = InstallCommands(cli_config)
    steps = commands.install_py_dependencies(pre=pre, dev=dev)
    on_fail = "Failed to install Python dependencies."
    on_success = "Python dependencies installed successfully."

    run_steps(steps, on_fail, on_success)


@install.command("assets")
@click.option(
    "--production/--development",
    "-p/-d",
    default=False,
    is_flag=True,
    help="Production mode copies statics/assets. Development mode symlinks"
    " statics/assets.",
)
@click.option("--re-lock", default=False, is_flag=True, help="relock javascript.")
@pass_cli_config
def install_assets(cli_config, production, re_lock):
    """Install assets."""
    commands = InstallCommands(cli_config)
    flask_env = "production" if production else "development"
    steps = commands.install_assets(flask_env, re_lock)
    on_fail = "Failed to install assets."
    on_success = "Assets installed successfully."

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
