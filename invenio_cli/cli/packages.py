# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""


import click

from ..commands import PackagesCommands
from .utils import pass_cli_config, run_steps


@click.group()
def packages():
    """Commands for package management."""


@packages.command()
@click.option('--pre', default=False, is_flag=True,
              help='Allows the installation of alpha releases.')
@click.option('--dev', default=False, is_flag=True,
              help='Include development devepencies.')
@pass_cli_config
def lock(cli_config, pre, dev):
    """Lock Python dependencies."""
    click.secho(
        f"Locking dependencies... Allow pre-releases: {pre}. " +
        f"Include dev-packages: {dev}.",
        fg="green"
    )
    steps = PackagesCommands.lock(pre, dev)
    on_fail = "Failed to lock dependencies."
    on_success = "Dependencies locked successfully."

    run_steps(steps, on_fail, on_success)


@packages.command()
@click.argument("packages", nargs=-1, type=str)
@pass_cli_config
def install(cli_config, packages):
    """Install one or a list of Python packages in the local environment."""
    if len(packages) < 1:
        raise click.UsageError("You must specify at least one package.")

    steps = PackagesCommands.install_packages(packages)
    on_fail = f"Failed to install packages {packages}."
    on_success = f"Packages {packages} installed successfully."

    run_steps(steps, on_fail, on_success)


@packages.command()
@pass_cli_config
def outdated(cli_config):
    """Show outdated Python dependencies."""
    raise click.UsageError("Not supported yet.")


@packages.command()
@pass_cli_config
def update(cli_config):
    """Update a single Python python package."""
    raise click.UsageError("Not supported yet.")
