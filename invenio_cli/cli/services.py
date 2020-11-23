# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""


import click

from ..helpers.cli_config import CLIConfig
from ..commands import Commands, ServicesCommands


# FIXME: This should be imported from cli.py
pass_cli_config = click.make_pass_decorator(CLIConfig, ensure=True)


@click.group()
def services():
    """Commands for services management."""


@services.command()
@pass_cli_config
def start(cli_config):
    """Start local services."""
    commands = ServicesCommands(cli_config)
    click.secho("Starting containers...", fg="green")
    commands.ensure_containers_running()
    click.secho('Started containers', fg='green')


@services.command()
@click.option('-f', '--force', default=False, is_flag=True,
              help='Force recreation of db tables, ES indices, queues...')
@click.option('-n', '--no-demo-data', default=False, is_flag=True,
              help='Disable the creation of demo data')
@pass_cli_config
def setup(cli_config, force, no_demo_data):
    """Setup local services."""
    # no_demo_data = False (default) means "YES to demo_data"
    demo_data = not no_demo_data

    commands = ServicesCommands(cli_config)
    commands.setup(force=force, demo_data=demo_data)


@services.command()
@pass_cli_config
def stop(cli_config):
    """Stop local services."""
    commands = Commands(cli_config)
    click.secho("Stopping containers...", fg="green")
    commands.stop()
    click.secho('Stopped containers', fg='green')


@services.command()
@click.option('-v', '--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
@pass_cli_config
def status(cli_config, verbose):
    """Checks if the services are up and running.

    NOTE: currently only ES, DB (postgresql/mysql) and redis are supported.
    """
    commands = Commands(cli_config)
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
@click.option('-v', '--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
@pass_cli_config
def Destroy(cli_config, verbose):
    """Destroy local services."""
    # FIXME: This destroy should not remove the venv
    commands = Commands(cli_config)
    click.secho(
        "Destroying containers, volumes, virtual environment...", fg="green")
    commands.destroy()
    click.secho('Instance destroyed', fg='green')
