# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2021 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import os
from pathlib import Path

import click

from ..commands import Commands, ContainersCommands, InstallCommands, \
    LocalCommands, RequirementsCommands, UpgradeCommands
from ..errors import InvenioCLIConfigError
from ..helpers.cli_config import CLIConfig
from ..helpers.cookiecutter_wrapper import CookiecutterWrapper
from .assets import assets
from .containers import containers
from .install import install
from .packages import packages
from .services import services
from .utils import calculate_instance_path, pass_cli_config, run_steps


@click.group()
@click.version_option()
@click.pass_context
def invenio_cli(ctx):
    """Initialize CLI context."""


invenio_cli.add_command(assets)
invenio_cli.add_command(containers)
invenio_cli.add_command(install)
invenio_cli.add_command(packages)
invenio_cli.add_command(services)


@invenio_cli.command('check-requirements')
@click.option('--development', '-d', default=False, is_flag=True,
              help='Check development requirements.')
def check_requirements(development):
    """Checks the system fulfills the pre-requirements."""
    click.secho("Checking pre-requirements...", fg="green")
    steps = RequirementsCommands.check(development)
    on_fail = "Pre requisites not met."
    on_success = "All requisites are fulfilled."

    run_steps(steps, on_fail, on_success)


@invenio_cli.command()
def shell():
    """Shell command."""
    Commands.shell()


@invenio_cli.command()
@click.option('--debug/--no-debug', '-d/', default=False, is_flag=True,
              help='Enable Flask development mode (default: disabled).')
def pyshell(debug):
    """Python shell command."""
    Commands.pyshell(debug=debug)


@invenio_cli.command()
@click.argument('flavour', type=click.Choice(['RDM'], case_sensitive=False),
                default='RDM', required=False)
@click.option('-t', '--template', required=False,
              help='Cookiecutter path or git url to template')
@click.option('-c', '--checkout', required=False,
              help='Branch, tag or commit to checkout if --template is a git url')  # noqa
def init(flavour, template, checkout):
    """Initializes the application according to the chosen flavour."""
    click.secho('Initializing {flavour} application...'.format(
        flavour=flavour), fg='green')

    template_checkout = (template, checkout)
    cookiecutter_wrapper = CookiecutterWrapper(flavour, template_checkout)

    try:
        click.secho("Running cookiecutter...", fg='green')
        project_dir = cookiecutter_wrapper.cookiecutter()

        click.secho("Writing invenio-invenio_cli config file...", fg='green')
        saved_replay = cookiecutter_wrapper.get_replay()
        instance_path = calculate_instance_path(project_dir)
        CLIConfig.write(project_dir, flavour, saved_replay, instance_path)

        click.secho("Creating logs directory...", fg='green')
        os.mkdir(Path(project_dir) / "logs")

    except Exception as e:
        click.secho(str(e), fg='red')

    finally:
        cookiecutter_wrapper.remove_config()


@invenio_cli.command()
@click.option('--host', '-h',  default='127.0.0.1',
              help='The interface to bind to.')
@click.option('--port', '-p',  default=5000,
              help='The port to bind to.')
@click.option('--debug/--no-debug', '-d/',  default=True, is_flag=True,
              help='Enable/disable debug mode including auto-reloading '
                   '(default: enabled).')
@click.option('--services/--no-services', '-s/-n',  default=True, is_flag=True,
              help='Enable/disable dockerized services (default: enabled).')
@pass_cli_config
def run(cli_config, host, port, debug, services):
    """Starts the local development server.

    NOTE: this only makes sense locally so no --local option
    """
    commands = LocalCommands(cli_config)
    commands.run(host=host, port=str(port), debug=debug, services=services)


@invenio_cli.command()
@pass_cli_config
def destroy(cli_config):
    """Removes all associated resources (containers, images, volumes)."""
    commands = Commands(cli_config)
    services = ContainersCommands(cli_config)
    click.secho(
        "Destroying containers, volumes, virtual environment...", fg="green")
    steps = commands.destroy()  # Destroy virtual environment
    steps.extend(services.destroy())  # Destroy services
    on_fail = "Failed to destroy instance. You can destroy only services " + \
              "using the services command: invenio-cli services destroy"
    on_success = "Instance destroyed."

    run_steps(steps, on_fail, on_success)


@invenio_cli.command()
@click.option('--script', required=True,
              help='The path of custom migration script.'
              )
def upgrade(script):
    """Upgrades the current instance to a newer version."""
    steps = UpgradeCommands.upgrade(script)
    on_fail = "Upgrade failed."
    on_success = "Upgrade sucessfull."

    run_steps(steps, on_fail, on_success)
