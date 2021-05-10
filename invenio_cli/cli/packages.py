# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""


import click

from ..commands import AssetsCommands, PackagesCommands
from .utils import pass_cli_config, run_steps


@click.group()
def packages():
    """Commands for package management."""


@packages.command()
@click.option('--pre', default=False, is_flag=True,
              help='Allows installation of alpha releases.')
@click.option('--dev', default=False, is_flag=True,
              help='Includes development dependencies.')
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
@click.option('-s', '--skip-build', default=False, is_flag=True,
              help='Do not rebuild the assets.')
@pass_cli_config
def install(cli_config, packages, skip_build):
    """Install one or a list of Python packages in the local environment."""
    if len(packages) < 1:
        raise click.UsageError("You must specify at least one package.")

    steps = PackagesCommands.install_packages(packages)

    on_fail = f"Failed to install packages {packages}."
    on_success = f"Packages {packages} installed successfully."

    run_steps(steps, on_fail, on_success)

    # FIXME: Migrate assets to steps.
    if not skip_build:
        click.secho("Rebuilding assets...")
        AssetsCommands(cli_config).update_statics_and_assets(
            force=True, flask_env='development')


@packages.command()
@pass_cli_config
def outdated(cli_config):
    """Show outdated Python dependencies."""
    steps = PackagesCommands.outdated_packages()

    on_fail = "Some of the packages need to be updated."
    on_success = "All packages are up to date."

    run_steps(steps, on_fail, on_success)


@packages.command()
@click.argument("version", required=False, type=str)
@pass_cli_config
def update(cli_config, version=None):
    """Update all or some Python python packages."""
    if version:
        db = cli_config.get_db_type()
        es = f"elasticsearch{cli_config.get_es_version()}"
        package = f"invenio-app-rdm[{db},{es}]~="
        steps = PackagesCommands.update_package_new_version(package, version)
        on_fail = f"Failed to update version {version}"
        on_success = f"Version {version} installed successfully."
    else:
        steps = PackagesCommands.update_packages()
        on_fail = "Failed to update packages."
        on_success = "Packages installed successfully."

    run_steps(steps, on_fail, on_success)
