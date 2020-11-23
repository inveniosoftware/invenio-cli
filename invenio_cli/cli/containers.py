# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import click

from ..helpers.cli_config import CLIConfig
from ..commands import Commands, ContainersCommands


# FIXME: This should be imported from cli.py
pass_cli_config = click.make_pass_decorator(CLIConfig, ensure=True)


@click.group()
def containers():
    """Containers management commands."""


@containers.command()
@click.option('--pull/--no-pull', default=True, is_flag=True,
              help='Download newer versions of the images (default: True).')
@click.option('--cache/--no-cache', default=True, is_flag=True,
              help='Disable cache (default=False).')
@pass_cli_config
def build(cli_config, pull, cache):
    """Build application and service images."""
    commands = ContainersCommands(cli_config)
    click.secho(
        f"Building images... Pull newer versions {pull}, use cache {cache}",
        fg="green"
    )
    commands.build(pull, cache)


@containers.command()
@click.option('-f', '--force', default=False, is_flag=True,
              help='Force recreation of db tables, ES indices, queues...')
@click.option('-n', '--no-demo-data', default=False, is_flag=True,
              help='Disable the creation of demo data')
@click.option('-s', '--stop-services', default=False, is_flag=True,
              help='Stop containers after setup.')
@pass_cli_config
def setup(cli_config, force, no_demo_data, stop_services):
    """Setup containerized services."""
    # no_demo_data = False (default) means "YES to demo_data"
    demo_data = not no_demo_data
    commands = ContainersCommands(cli_config)
    click.secho(
        f"Setting up services with force {force}, demo data {demo_data} "+
        f"and stop after setup {stop_services}...",
        fg="green"
    )
    commands.setup(force, demo_data, stop_services)


@containers.command()
@click.option('--lock/--skip-lock', default=False, is_flag=True,
              help='Lock Python dependencies (default=False).')
@click.option('--build/--no-build', default=False, is_flag=True,
              help='Build images (default=False).')
@click.option('--setup/--no-setup', default=False, is_flag=True,
              help='Setup services (default=False). ' +
                   'It will run with force=True.')
@click.option('--demo-data/--no-demo-data', default=False, is_flag=True,
              help='Include demo records (default=False), requires --setup.')
@click.option('--services/--no-services', '-s/-n',  default=True, is_flag=True,
              help='Enable/disable dockerized services (default: enabled).')
@pass_cli_config
def start(cli_config, lock, build, setup, demo_data, services):
    """Start containerized services and application."""
    commands = ContainersCommands(cli_config)
    click.secho("Starting InvenioRDM instance...")
    commands.start(lock, build, setup, demo_data, services)
    click.secho('Instance running!\nVisit https://127.0.0.1', fg='green')


@containers.command()
@pass_cli_config
def stop(cli_config):
    """Stop containerized services and application."""
    commands = Commands(cli_config)
    click.secho("Stopping containers...", fg="green")
    commands.stop()
    click.secho('Stopped containers', fg='green')


@containers.command()
@pass_cli_config
def destroy(cli_config):
    """Destroy containerized services and application."""
    # FIXME: This destroy should not remove the venv
    commands = Commands(cli_config)
    click.secho(
        "Destroying containers, volumes, virtual environment...", fg="green")
    commands.destroy()
    click.secho('Instance destroyed', fg='green')
