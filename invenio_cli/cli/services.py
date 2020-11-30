# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""


import click

from ..commands import Commands, ServicesCommands
from ..helpers.cli_config import CLIConfig
from .utils import pass_cli_config, run_steps


@click.group()
def services():
    """Commands for services management."""


@services.command()
@pass_cli_config
def start(cli_config):
    """Start local services."""
    click.secho("Starting containers...", fg="green")
    commands = ServicesCommands(cli_config)
    steps = commands.start()
    on_fail = "Failed to start services."
    on_success = "Services started successfully."

    run_steps(steps, on_fail, on_success)


@services.command()
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
    """Setup local services."""
    # no_demo_data = False (default) means "YES to demo_data"
    demo_data = not no_demo_data
    commands = ServicesCommands(cli_config)
    steps = commands.setup(force, demo_data, stop_services, services)
    on_fail = "Failed to setup services."
    on_success = "Successfully setup all services."

    run_steps(steps, on_fail, on_success)


# FIXME: Duplicated code from containers.py
@services.command()
@click.option('-v', '--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
@pass_cli_config
def status(cli_config, verbose):
    """Checks if the services are up and running.

    NOTE: currently only ES, DB (postgresql/mysql) and redis are supported.
    """
    commands = ServicesCommands(cli_config)
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


@services.command()
@pass_cli_config
def stop(cli_config):
    """Stop local services."""
    commands = ServicesCommands(cli_config)
    steps = commands.stop()
    on_fail = "Failed to stop containers."
    on_success = "Stopped containers."

    run_steps(steps, on_fail, on_success)


@services.command()
@pass_cli_config
def destroy(cli_config):
    """Destroy developement services."""
    commands = ServicesCommands(cli_config)
    click.secho("Destroying services' containers, volumes...", fg="green")
    steps = commands.destroy()
    on_fail = "Failed to destroy services' containers."
    on_success = "Services' containers destroyed."

    run_steps(steps, on_fail, on_success)
