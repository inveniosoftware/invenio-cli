# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import click

from ..commands import ContainersCommands
from .utils import pass_cli_config, run_steps


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
    steps = commands.build(pull, cache)
    on_fail = "Failed to build images."
    on_success = "Images built successfully."

    run_steps(steps, on_fail, on_success)


@containers.command()
@click.option('-f', '--force', default=False, is_flag=True,
              help='Force recreation of db tables, ES indices, queues...')
@click.option('-N', '--no-demo-data', default=False, is_flag=True,
              help='Disable the creation of demo data')
@click.option('--stop-services', default=False, is_flag=True,
              help='Stop containers after setup.')
@click.option('--services/--no-services', '-s/-n',  default=True, is_flag=True,
              help='Enable/disable dockerized services (default: enabled).')
@pass_cli_config
def setup(cli_config, force, no_demo_data, stop_services, services):
    """Setup containerized services."""
    # no_demo_data = False (default) means "YES to demo_data"
    demo_data = not no_demo_data
    commands = ContainersCommands(cli_config)
    click.secho(
        f"Setting up services with force {force}, demo data {demo_data} " +
        f"and stop after setup {stop_services}...",
        fg="green"
    )

    steps = commands.setup(force, demo_data, stop_services, services)
    on_fail = "Failed to setup services."
    on_success = "Services setup successfully."

    run_steps(steps, on_fail, on_success)


# FIXME: Duplicated code from services.py
@containers.command()
@click.option('-v', '--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
@pass_cli_config
def status(cli_config, verbose):
    """Checks if the services are up and running.

    NOTE: currently only ES, DB (postgresql/mysql) and redis are supported.
    """
    commands = ContainersCommands(cli_config)
    services = ["redis", cli_config.get_db_type(), "es"]
    statuses = commands.status(services=services, verbose=verbose)

    messages = [
        {"message": "{}: up and running.", "fg": "green"},
        {"message": "{}: unable to connect or bad response.", "fg": "red"},
        {"message": "{}: no healthcheck function defined.", "fg": "yellow"}
    ]

    for idx, status in enumerate(statuses):
        message = messages[status]
        click.secho(
            message=message.get("message").format(services[idx]),
            fg=message.get("fg")
        )


@containers.command()
@click.option('--lock/--skip-lock', default=False, is_flag=True,
              help='Lock Python dependencies (default=False).')
@click.option('--build/--no-build', default=False, is_flag=True,
              help='Build images (default=False).')
@click.option('--setup/--no-setup', default=False, is_flag=True,
              help='Setup services (default=False). ' +
                   'It will run with force=True.')
@click.option('--demo-data/--no-demo-data', default=True, is_flag=True,
              help='Include demo records (default=True), requires --setup.')
@click.option('--services/--no-services', '-s/-n',  default=True, is_flag=True,
              help='Enable/disable dockerized services (default: enabled).')
@pass_cli_config
def start(cli_config, lock, build, setup, demo_data, services):
    """Start containerized services and application."""
    commands = ContainersCommands(cli_config)
    click.secho("Starting InvenioRDM instance...")
    steps = commands.start(lock, build, setup, demo_data, services)
    on_fail = "Failed to start containerized instance."
    on_success = "Instance running!\nVisit https://127.0.0.1"

    run_steps(steps, on_fail, on_success)


@containers.command()
@pass_cli_config
def stop(cli_config):
    """Stop containerized services and application."""
    commands = ContainersCommands(cli_config)
    steps = commands.stop()
    on_fail = "Failed to stop containers."
    on_success = "Stopped containers."

    run_steps(steps, on_fail, on_success)


@containers.command()
@pass_cli_config
def destroy(cli_config):
    """Destroy containerized services and application."""
    commands = ContainersCommands(cli_config)
    click.secho(
        "Destroying containers, volumes, virtual environment...", fg="green")
    steps = commands.destroy()
    on_fail = "Failed to destroy instance's containers."
    on_success = "Instance' containers destroyed."

    run_steps(steps, on_fail, on_success)
