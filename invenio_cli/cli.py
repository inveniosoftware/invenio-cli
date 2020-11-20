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
from .errors import InvenioCLIConfigError
from .helpers.cli_config import CLIConfig
from .helpers.cookiecutter_wrapper import CookiecutterWrapper

pass_cli_config = click.make_pass_decorator(CLIConfig, ensure=True)


@click.group()
@click.version_option()
@click.pass_context
def cli(ctx):
    """Initialize CLI context."""
    # Config loading is not needed when initializing
    if ctx.invoked_subcommand != "init":
        try:
            ctx.cli_config = CLIConfig()
        except InvenioCLIConfigError as e:
            click.secho(e.message, fg="red")


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
@pass_cli_config
def install(cli_config, pre, lock, production):
    """Installs the  project locally.

    Installs dependencies, creates instance directory,
    links invenio.cfg + templates, copies images and other statics and finally
    builds front-end assets.
    """
    commands = LocalCommands(cli_config)
    commands.install(
        pre=pre,
        lock=lock,
        flask_env='production' if production else 'development'
    )


@cli.command()
@click.option('-f', '--force', default=False, is_flag=True,
              help='Force recreation of db tables, ES indices, queues...')
@pass_cli_config
def services(cli_config, force):
    """Starts DB, ES, queue and cache services and ensures they are setup.

    --force destroys and resets services
    """
    commands = LocalCommands(cli_config)
    commands.services(force=force)


@cli.command()
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


@cli.command()
@click.option('--pre', default=False, is_flag=True,
              help='If specified, allows the installation of alpha releases')
@click.option('-f', '--force', default=False, is_flag=True,
              help='Force recreation of db tables, ES indices, queues...')
@click.option('--install-js/--no-install-js', default=True, is_flag=True,
              help="(re-)Install JS dependencies, defaults to True")
@pass_cli_config
def containerize(cli_config, pre, force, install_js):
    """Setup and run all containers (docker-compose.full.yml).

    Think of it as a production compilation build + running.
    """
    commands = ContainersCommands(cli_config)

    commands.containerize(pre=pre, force=force, install=install_js)


@cli.command()
@click.option('--local/--containers', default=True, is_flag=True,
              help='Which environment to build, it defaults to local')
@pass_cli_config
def demo(cli_config, local):
    """Populates instance with demo records."""
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
@pass_cli_config
def run(cli_config, host, port, debug):
    """Starts the local development server.

    NOTE: this only makes sense locally so no --local option
    """
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
@pass_cli_config
def update(cli_config, force, production):
    """Updates the current application static/assets files."""
    commands = LocalCommands(cli_config)
    commands.update_statics_and_assets(
        force=force,
        flask_env='production' if production else 'development'
    )


@assets.command()
@pass_cli_config
def watch(cli_config):
    """Watch assets files for changes and rebuild."""
    commands = LocalCommands(cli_config)
    commands.watch_assets()


@assets.command('install-module')
@click.argument('path', type=click.Path(exists=True))
@pass_cli_config
def install_module(cli_config, path):
    """Install and link a React module."""
    commands = LocalCommands(cli_config)
    commands.link_js_module(path)


@assets.command('watch-module')
@click.option('--link', '-l', default=False, is_flag=True,
              help='Link the module.')
@click.argument('path', type=click.Path(exists=True))
@pass_cli_config
def watch_module(cli_config, path, link):
    """Watch a React module."""
    commands = LocalCommands(cli_config)
    commands.watch_js_module(path, link=link)


@cli.command()
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


@cli.command()
@pass_cli_config
def stop(cli_config):
    """Stops containers."""
    commands = Commands(cli_config)
    click.secho("Stopping containers...", fg="green")
    commands.stop()
    click.secho('Stopped containers', fg='green')


@cli.command()
@click.option('-v', '--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def upgrade(verbose):
    """Upgrades the current application to the specified newer version."""
    click.secho('TODO: Implement upgrade command', fg='red')


@cli.command()
@pass_cli_config
def shell(cli_config, ):
    """Shell command."""
    commands = Commands(cli_config)
    commands.shell()


@cli.command()
@click.option(
    '--debug/--no-debug', '-d/', default=False, is_flag=True,
    help='Enable Flask development mode (default: disabled).'
)
@pass_cli_config
def pyshell(cli_config, debug):
    """Python shell command."""
    commands = Commands(cli_config)
    commands.pyshell(debug=debug)


@cli.group()
def ext():
    """Commands for development."""


@ext.command('module-install')
@click.argument("modules", nargs=-1, type=str)
@pass_cli_config
def module_install(cli_config, modules):
    """Install a Python module in development mode."""
    commands = LocalCommands(cli_config)
    commands.install_modules(modules)
