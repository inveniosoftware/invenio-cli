# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import os
from pathlib import Path

import click

from ..commands import Commands, InstallCommands, LocalCommands
from ..errors import InvenioCLIConfigError
from ..helpers.cli_config import CLIConfig
from ..helpers.cookiecutter_wrapper import CookiecutterWrapper
from .assets import assets
from .containers import containers
from .packages import packages
from .services import services

pass_cli_config = click.make_pass_decorator(CLIConfig, ensure=True)


@click.group()
@click.version_option()
@click.pass_context
def invenio_cli(ctx):
    """Initialize CLI context."""
    # Config loading is not needed when initializing
    if ctx.invoked_subcommand != "init":
        try:
            ctx.cli_config = CLIConfig()
        except InvenioCLIConfigError as e:
            click.secho(e.message, fg="red")


invenio_cli.add_command(assets)
invenio_cli.add_command(containers)
invenio_cli.add_command(packages)
invenio_cli.add_command(services)


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
        CLIConfig.write(project_dir, flavour, saved_replay)

        click.secho("Creating logs directory...", fg='green')
        os.mkdir(Path(project_dir) / "logs")

    except Exception as e:
        click.secho(str(e), fg='red')

    finally:
        cookiecutter_wrapper.remove_config()


@invenio_cli.command()
@click.option('--pre', default=False, is_flag=True,
              help='If specified, allows the installation of alpha releases')
@click.option(
    '--production/--development', '-p/-d', default=True, is_flag=True,
    help='Production mode copies statics/assets. Development mode symlinks'
         ' statics/assets.'
)
@pass_cli_config
def install(cli_config, pre, production):
    """Installs the  project locally.

    Installs dependencies, creates instance directory,
    links invenio.cfg + templates, copies images and other statics and finally
    builds front-end assets.
    """
    commands = InstallCommands(cli_config)
    click.secho()

    result = commands.install(
        pre=pre,
        flask_env='production' if production else 'development'
    )

    if result.status_code > 0:
        click.secho(
            "Failed to install dependencies.\nErrors: {}\nOutput: {}",
            fg="red"
        )
    else:
        click.secho("Dependencies installed successfully.", fg="green")


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
@click.option('-v', '--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
@pass_cli_config
def destroy(cli_config, verbose):
    """Removes all associated resources (containers, images, volumes)."""
    commands = Commands(cli_config)
    click.secho(
        "Destroying containers, volumes, virtual environment...", fg="green")
    commands.destroy()
    click.secho('Instance destroyed', fg='green')


@invenio_cli.command()
@click.option('-v', '--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def upgrade(verbose):
    """Upgrades the current application to the specified newer version."""
    click.secho('TODO: Implement upgrade command', fg='red')


@invenio_cli.command()
@pass_cli_config
def shell(cli_config, ):
    """Shell command."""
    commands = Commands(cli_config)
    commands.shell()


@invenio_cli.command()
@click.option(
    '--debug/--no-debug', '-d/', default=False, is_flag=True,
    help='Enable Flask development mode (default: disabled).'
)
@pass_cli_config
def pyshell(cli_config, debug):
    """Python shell command."""
    commands = Commands(cli_config)
    commands.pyshell(debug=debug)
