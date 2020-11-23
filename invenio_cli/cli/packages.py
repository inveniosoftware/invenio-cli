# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""


import click

from ..helpers.cli_config import CLIConfig
from ..commands import Commands, InstallCommands


# FIXME: This should be imported from cli.py
pass_cli_config = click.make_pass_decorator(CLIConfig, ensure=True)


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
    commands = Commands(cli_config)
    result = commands.lock(pre, dev)

    if result.status_code > 0:
        click.secho(
            "Failed to lock dependencies.\nErrors: {}\nOutput: {}", fg="red")
    else:
        click.secho("Dependencies locked successfully.", fg="green")


@packages.command()
@click.argument("packages", nargs=-1, type=str)
@pass_cli_config
def install(cli_config, packages):
    """Install one or a list of Python packages in the local environment."""
    commands = InstallCommands(cli_config)
    result = commands.install_packages(packages)

    if result.status_code > 0:
        click.secho(
            "Failed to lock dependencies.\nErrors: {}\nOutput: {}", fg="red")
    else:
        click.secho("Packages {packages} installed successfully.", fg="green")


@packages.command()
@pass_cli_config
def outdated(cli_config):
    """Show outdated Python dependencies."""
    click.secho("Not supported yet.", fg="red")


@packages.command()
@pass_cli_config
def update(cli_config):
    """Update a single Python python package."""
    click.secho("Not supported yet.", fg="red")
