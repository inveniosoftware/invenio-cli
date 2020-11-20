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

from .commands import Commands, ContainersCommands, LocalCommands
from .helpers.cli_config import CLIConfig
from .helpers.cookiecutter_wrapper import CookiecutterWrapper


@click.group()
@click.version_option()
def cli():
    """Initialize CLI context."""


@cli.command()
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

        click.secho("Writing invenio-cli config file...", fg='green')
        saved_replay = cookiecutter_wrapper.get_replay()
        CLIConfig.write(project_dir, flavour, saved_replay)

        click.secho("Creating logs directory...", fg='green')
        os.mkdir(Path(project_dir) / "logs")

    except Exception as e:
        click.secho(str(e), fg='red')

    finally:
        cookiecutter_wrapper.remove_config()


@cli.command()
@click.option('--pre', default=False, is_flag=True,
              help='If specified, allows the installation of alpha releases')
@click.option('--lock/--skip-lock', default=True, is_flag=True,
              help='Lock dependencies or avoid this step')
@click.option(
    '--production/--development', '-p/-d', default=True, is_flag=True,
    help='Production mode copies statics/assets. Development mode symlinks'
         ' statics/assets.'
)
def install(pre, lock, production):
    """Installs the  project locally.

    Installs dependencies, creates instance directory,
    links invenio.cfg + templates, copies images and other statics and finally
    builds front-end assets.
    """
    cli_config = CLIConfig()
    commands = LocalCommands(cli_config)
    commands.install(
        pre=pre,
        lock=lock,
        flask_env='production' if production else 'development'
    )


@cli.command()
@click.option('-f', '--force', default=False, is_flag=True,
              help='Force recreation of db tables, ES indices, queues...')
def services(force):
    """Starts DB, ES, queue and cache services and ensures they are setup.

    --force destroys and resets services
    """
    cli_config = CLIConfig()
    commands = LocalCommands(cli_config)
    commands.services(force=force)


@cli.command()
@click.option('-v', '--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def status(verbose):
    """Checks if the services are up and running.

    NOTE: currently only ES, DB (postgresql/mysql) and redis are supported.
    """
    cli_config = CLIConfig()
    commands = Commands(cli_config)
    commands.status(
        services=["redis", cli_config.get_db_type(), "es"], verbose=verbose)


@cli.command()
@click.option('--pre', default=False, is_flag=True,
              help='If specified, allows the installation of alpha releases')
@click.option('-f', '--force', default=False, is_flag=True,
              help='Force recreation of db tables, ES indices, queues...')
@click.option('--install-js/--no-install-js', default=True, is_flag=True,
              help="(re-)Install JS dependencies, defaults to True")
def containerize(pre, force, install_js):
    """Setup and run all containers (docker-compose.full.yml).

    Think of it as a production compilation build + running.
    """
    cli_config = CLIConfig()
    commands = ContainersCommands(cli_config)

    commands.containerize(pre=pre, force=force, install=install_js)


@cli.command()
@click.option('--local/--containers', default=True, is_flag=True,
              help='Which environment to build, it defaults to local')
def demo(local):
    """Populates instance with demo records."""
    cli_config = CLIConfig()
    commands = LocalCommands(cli_config)
    commands.demo()


@cli.command()
@click.option('--host', '-h',  default='127.0.0.1',
              help='The interface to bind to.')
@click.option('--port', '-p',  default=5000,
              help='The port to bind to.')
@click.option('--debug/--no-debug', '-d/',  default=True, is_flag=True,
              help='Enable/disable debug mode including auto-reloading '
                   '(default: enabled).')
def run(host, port, debug):
    """Starts the local development server.

    NOTE: this only makes sense locally so no --local option
    """
    cli_config = CLIConfig()
    commands = LocalCommands(cli_config)
    commands.run(host=host, port=str(port), debug=debug)


@cli.group()
def assets():
    """Statics and assets management commands."""


@assets.command()
@click.option('--force', '-f', default=False, is_flag=True,
              help='Force the full recreation the assets and statics.')
@click.option(
    '--production/--development', '-p/-d', default=True, is_flag=True,
    help='Production mode copies files. Development mode symlinks files.'
)
def update(force, production):
    """Updates the current application static/assets files."""
    cli_config = CLIConfig()
    commands = LocalCommands(cli_config)
    commands.update_statics_and_assets(
        force=force,
        flask_env='production' if production else 'development'
    )


@assets.command()
def watch():
    """Watch assets files for changes and rebuild."""
    cli_config = CLIConfig()
    commands = LocalCommands(cli_config)
    commands.watch_assets()


@assets.command('install-module')
@click.argument('path', type=click.Path(exists=True))
def install_module(path):
    """Install and link a React module."""
    cli_config = CLIConfig()
    commands = LocalCommands(cli_config)
    commands.link_js_module(path)


@assets.command('watch-module')
@click.option('--link', '-l', default=False, is_flag=True,
              help='Link the module.')
@click.argument('path', type=click.Path(exists=True))
def watch_module(path, link):
    """Watch a React module."""
    cli_config = CLIConfig()
    commands = LocalCommands(cli_config)
    commands.watch_js_module(path, link=link)


@cli.command()
@click.option('-v', '--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def destroy(verbose):
    """Removes all associated resources (containers, images, volumes)."""
    cli_config = CLIConfig()
    commands = Commands(cli_config)
    commands.destroy()


@cli.command()
def stop():
    """Stops containers."""
    cli_config = CLIConfig()
    commands = Commands(cli_config)
    commands.stop()


@cli.command()
@click.option('-v', '--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def upgrade(verbose):
    """Upgrades the current application to the specified newer version."""
    click.secho('TODO: Implement upgrade command', fg='red')


@cli.command()
def shell():
    """Shell command."""
    cli_config = CLIConfig()
    commands = Commands(cli_config)
    commands.shell()


@cli.command()
@click.option(
    '--debug/--no-debug', '-d/', default=False, is_flag=True,
    help='Enable Flask development mode (default: disabled).'
)
def pyshell(debug):
    """Python shell command."""
    cli_config = CLIConfig()
    commands = Commands(cli_config)
    commands.pyshell(debug=debug)


@cli.group()
def ext():
    """Commands for development."""


@ext.command('module-install')
@click.argument("modules", nargs=-1, type=str)
def module_install(modules):
    """Install a Python module in development mode."""
    cli_config = CLIConfig()
    commands = LocalCommands(cli_config)
    commands.install_modules(modules)
