# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import logging
import os
import subprocess
from configparser import ConfigParser
from pathlib import Path

import click
from cookiecutter.exceptions import OutputDirExistsException
from cookiecutter.main import cookiecutter

from .helpers import CookiecutterConfig, DockerCompose, LogPipe, bootstrap, \
    get_created_files
from .helpers import server as scripts_server
from .helpers import setup

CONFIG_FILENAME = '.invenio'
CLI_SECTION = 'cli'
# NOTE: If modifying the list check the impact in the `init` command.
CLI_ITEMS = ['project_name', 'flavour', 'logfile']
COOKIECUTTER_SECTION = 'cookiecutter'
FILES_SECTION = 'files'

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}


class InvenioCli(object):
    """Current application building properties."""

    def __init__(self, flavour=None, loglevel=LEVELS['warning'],
                 verbose=False):
        """Initialize builder.

        :param flavour: Flavour name.
        """
        self.flavour = None
        self.project_name = None
        self.config = ConfigParser()
        self.config.read(CONFIG_FILENAME)
        self.verbose = verbose
        self.loglevel = loglevel
        self.logfile = None

        # There is a .invenio config file
        if os.path.isfile(CONFIG_FILENAME):
            try:
                for item in CLI_ITEMS:
                    setattr(self, item, self.config[CLI_SECTION][item])
            except KeyError:
                logging.error(
                    '{item} not configured in CLI section'.format(item=item))
                exit(1)
            # Provided flavour differs from the one in .invenio
            if flavour and flavour != self.flavour:
                logging.error('Config flavour in .invenio differs from ' +
                              'the specified')
                exit(1)
        elif flavour:
            # There is no .invenio file but the flavour was provided via CLI
            self.flavour = flavour
        else:
            # No value for flavour in .invenio nor CLI
            logging.error('No flavour specified.')
            exit(1)


@click.group()
def cli():
    """Initialize CLI context."""


@cli.command()
@click.option('--flavour', type=click.Choice(['RDM'], case_sensitive=False),
              default=None, required=False)
@click.option('--log-level', required=False, default='warning',
              type=click.Choice(list(LEVELS.keys()), case_sensitive=False))
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def init(flavour, log_level, verbose):
    """Initializes the application according to the chosen flavour."""
    click.secho('Initializing {flavour} application...'.format(
        flavour=flavour), fg='green')

    # Create config object
    invenio_cli = InvenioCli(
        flavour=flavour,
        loglevel=LEVELS[log_level],
        verbose=verbose
    )

    # Process Cookiecutter
    cookie_config = CookiecutterConfig()

    try:
        context = cookiecutter(
            config_file=cookie_config.create_and_dump_config(),
            **cookie_config.repository(flavour)
        )

        file_fullpath = Path(context) / CONFIG_FILENAME

        with open(file_fullpath, 'w') as configfile:
            # Open config file
            config = invenio_cli.config
            config.read(CONFIG_FILENAME)

            # CLI parameters
            config[CLI_SECTION] = {}
            config[CLI_SECTION]['flavour'] = flavour
            config[CLI_SECTION]['project_name'] = os.path.basename(context)
            config[CLI_SECTION]['logfile'] = \
                '{path}/logs/invenio-cli.log'.format(path=context)

            # Cookiecutter user input
            config[COOKIECUTTER_SECTION] = {}
            replay = cookie_config.get_replay()
            for key, value in replay[COOKIECUTTER_SECTION].items():
                config[COOKIECUTTER_SECTION][key] = value
            # Generated files
            config[FILES_SECTION] = get_created_files(
                    config[COOKIECUTTER_SECTION]['project_shortname'])

            config.write(configfile)

            click.secho("Creating logs directory...")
            os.mkdir(Path(config[CLI_SECTION]['project_name']) / "logs")

    except OutputDirExistsException as e:
        click.secho(str(e), fg='red')

    finally:
        cookie_config.remove_config()


@cli.command()
@click.option('--dev/--prod', default=True, is_flag=True,
              help='Which environment to build, it defaults to development')
@click.option('--base/--skip-base', default=True, is_flag=True,
              help='If specified, it will build the base docker image ' +
                   '(not compatible with --dev)')
@click.option('--pre', default=False, is_flag=True,
              help='If specified, allows the installation of alpha releases')
@click.option('--lock/--skip-lock', default=True, is_flag=True,
              help='Lock dependencies or avoid this step')
@click.option('--log-level', required=False, default='warning',
              type=click.Choice(list(LEVELS.keys()), case_sensitive=False))
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def build(base, pre, dev, lock, log_level, verbose):
    """Locks the dependencies and builds the corresponding docker images."""
    # Create config object
    invenio_cli = InvenioCli(
        loglevel=LEVELS[log_level],
        verbose=verbose
    )

    click.secho('Building {flavour} application...'.format(
                flavour=invenio_cli.flavour), fg='green')

    # Initialize docker client
    docker_compose = DockerCompose(dev=dev, loglevel=invenio_cli.loglevel,
                                   logfile=invenio_cli.logfile)
    if lock:
        _lock_dependencies(invenio_cli, pre)

    bootstrap(dev=dev, pre=pre, base=base,
              docker_helper=docker_compose,
              app_name=invenio_cli.project_name,
              verbose=invenio_cli.verbose,
              loglevel=invenio_cli.loglevel,
              logfile=invenio_cli.logfile)

    click.secho('Creating {mode} services...'
                .format(mode='development' if dev else 'semi-production'),
                fg='green')
    docker_compose.create_images()


def _lock_dependencies(cli_obj, pre):
    # Open logging pipe
    logpipe = LogPipe(cli_obj.loglevel, cli_obj.logfile)
    # Lock dependencies
    click.secho('Locking dependencies...', fg='green')
    command = ['pipenv', 'lock']
    if pre:
        command.append('--pre')
    # No need for `with` context since call is a blocking op
    subprocess.call(command, stdout=logpipe, stderr=logpipe)
    # Close logging pipe
    logpipe.close()


@cli.command()
@click.option('--dev/--prod', default=True, is_flag=True,
              help='Which environment to build, it defaults to development')
@click.option('--force', default=False, is_flag=True,
              help='Delete all content from the database, ES indexes, queues')
@click.option('--log-level', required=False, default='warning',
              type=click.Choice(list(LEVELS.keys()), case_sensitive=False))
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def setup(dev, force, log_level, verbose):
    """Sets up the application for the first time (DB, ES, queue, etc.)."""
    # Create config object
    invenio_cli = InvenioCli(
        loglevel=LEVELS[log_level],
        verbose=verbose
    )

    click.secho('Setting up environment for {flavour} application...'
                .format(flavour=invenio_cli.flavour), fg='green')

    # Initialize docker client
    docker_compose = DockerCompose(dev=dev, loglevel=invenio_cli.loglevel,
                                   logfile=invenio_cli.logfile)

    setup(dev=dev, force=force,
          docker_helper=docker_compose,
          app_name=invenio_cli.project_name,
          verbose=invenio_cli.verbose,
          loglevel=invenio_cli.loglevel,
          logfile=invenio_cli.logfile)


@cli.command()
@click.option('--dev/--prod', default=True, is_flag=True,
              help='Which environment to build, it defaults to development')
@click.option('--start/--stop', default=True, is_flag=True,
              help='Start or Stop application and services')
@click.option('--log-level', required=False, default='warning',
              type=click.Choice(list(LEVELS.keys()), case_sensitive=False))
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def server(dev, start, log_level, verbose):
    """Starts the application server."""
    # Create config object
    invenio_cli = InvenioCli(
        loglevel=LEVELS[log_level],
        verbose=verbose
    )

    docker_compose = DockerCompose(dev=dev, bg=verbose,
                                   logfile=invenio_cli.logfile,
                                   loglevel=invenio_cli.loglevel)
    if start:
        click.secho('Booting up server...', fg='green')
        scripts_server(dev, docker_compose, invenio_cli.loglevel,
                       invenio_cli.logfile, invenio_cli.verbose)
    else:
        click.secho('Stopping server...', fg="green")
        docker_compose.stop_containers()


@cli.command()
@click.option('--dev/--prod', default=True, is_flag=True,
              help='Which environment to build, it defaults to development')
@click.option('--log-level', required=False, default='warning',
              type=click.Choice(list(LEVELS.keys()), case_sensitive=False))
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def destroy(dev, log_level, verbose):
    """Removes all associated resources (containers, images, volumes)."""
    # Create config object
    invenio_cli = InvenioCli(
        loglevel=LEVELS[log_level],
        verbose=verbose
    )

    click.secho('Destroying {flavour} application...'
                .format(flavour=invenio_cli.flavour), fg='green')
    docker_compose = DockerCompose(dev=dev, loglevel=invenio_cli.loglevel,
                                   logfile=invenio_cli.logfile)
    docker_compose.destroy_containers()


@cli.command()
@click.option('--log-level', required=False, default='warning',
              type=click.Choice(list(LEVELS.keys()), case_sensitive=False))
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode, puts the application in debug mode on the \
                  terminal output.')
def upgrade(log_level, verbose):
    """Upgrades the current application to the specified newer version."""
    # Create config object
    invenio_cli = InvenioCli(
        loglevel=LEVELS[log_level],
        verbose=verbose
    )

    click.secho('Upgrading server for {flavour} application...'
                .format(flavour=invenio_cli.flavour), fg='green')
    click.secho('ERROR: Not supported yet...', fg='red')
