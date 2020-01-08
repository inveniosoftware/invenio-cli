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

from .helpers import CookiecutterConfig, DockerHelper, LoggingConfig, \
    LogPipe, bootstrap, build_assets, get_created_files, \
    populate_demo_records
from .helpers import server as scripts_server
from .helpers import setup as scripts_setup
from .helpers import update_statics

CONFIG_FILENAME = '.invenio'
CLI_SECTION = 'cli'
CLI_PROJECT_NAME = 'project_shortname'
CLI_FLAVOUR = 'flavour'
CLI_LOGFILE = 'logfile'
COOKIECUTTER_SECTION = 'cookiecutter'
FILES_SECTION = 'files'


class InvenioCli(object):
    """Current application building properties."""

    def __init__(self, flavour=None, verbose=False):
        """Initialize builder.

        :param flavour: Flavour name.
        """
        self.flavour = None
        self.project_shortname = None
        self.log_config = None
        self.config = ConfigParser()
        self.config.read(CONFIG_FILENAME)

        # There is a .invenio config file
        if os.path.isfile(CONFIG_FILENAME):
            try:
                self.flavour = self.config[CLI_SECTION][CLI_FLAVOUR]
                self.project_shortname = \
                    self.config[CLI_SECTION][CLI_PROJECT_NAME]
                self.log_config = LoggingConfig(
                    logfile=self.config[CLI_SECTION][CLI_LOGFILE],
                    verbose=verbose
                )
            except KeyError:
                logging.error(
                    '{0}, {1} or {2} not configured in CLI section'.format(
                        CLI_PROJECT_NAME, CLI_LOGFILE, CLI_FLAVOUR
                    ))
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
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def init(flavour, verbose):
    """Initializes the application according to the chosen flavour."""
    click.secho('Initializing {flavour} application...'.format(
        flavour=flavour), fg='green')

    # Create config object
    invenio_cli = InvenioCli(flavour=flavour, verbose=verbose)

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
            config[CLI_SECTION]['project_shortname'] = \
                os.path.basename(context)
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
            os.mkdir(Path(config[CLI_SECTION]['project_shortname']) / "logs")

    except OutputDirExistsException as e:
        click.secho(str(e), fg='red')

    finally:
        cookie_config.remove_config()


@cli.command()
@click.option('--local/--containers', default=True, is_flag=True,
              help='Which environment to build, it defaults to local')
@click.option('--pre', default=False, is_flag=True,
              help='If specified, allows the installation of alpha releases')
@click.option('--lock/--skip-lock', default=True, is_flag=True,
              help='Lock dependencies or avoid this step')
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def build(pre, local, lock, verbose):
    """Locks the dependencies and builds the corresponding docker images."""
    # Create config object
    invenio_cli = InvenioCli(verbose=verbose)

    click.secho('Building {flavour} application...'.format(
                flavour=invenio_cli.flavour), fg='green')

    # Initialize docker client
    docker_helper = DockerHelper(local=local,
                                 log_config=invenio_cli.log_config)
    if lock:
        _lock_dependencies(invenio_cli.log_config, pre)

    bootstrap(local=local, pre=pre,
              docker_helper=docker_helper,
              project_shortname=invenio_cli.project_shortname,
              log_config=invenio_cli.log_config)

    click.secho('Creating services...', fg='green')
    docker_helper.create_images()


@cli.command()
@click.option('--local/--containers', default=True, is_flag=True,
              help='Which environment to build, it defaults to local')
@click.option('--statics/--skip-statics', default=True, is_flag=True,
              help='Regenerate static files or skip this step.')
@click.option('--webpack/--skip-webpack', default=True, is_flag=True,
              help='Build the application using webpack or skip this step.')
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def assets(local, statics, webpack, verbose):
    """Locks the dependencies and builds the corresponding docker images."""
    # Create config object
    invenio_cli = InvenioCli(verbose=verbose)

    click.secho('Generating assets...'.format(
                flavour=invenio_cli.flavour), fg='green')

    build_assets(local, statics, webpack, invenio_cli.log_config)


def _lock_dependencies(log_config, pre):
    # Open logging pipe
    logpipe = LogPipe(log_config)
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
@click.option('--local/--containers', default=True, is_flag=True,
              help='Which environment to build, it defaults to local')
@click.option('--force', default=False, is_flag=True,
              help='Delete all content from the database, ES indexes, queues')
@click.option('--stop-containers', default=False, is_flag=True, required=False,
              help='Stop containers when finishing the setup operations.')
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def setup(local, force, stop_containers, verbose):
    """Sets up the application for the first time (DB, ES, queue, etc.)."""
    # Create config object
    invenio_cli = InvenioCli(verbose=verbose)

    click.secho('Setting up environment for {flavour} application...'
                .format(flavour=invenio_cli.flavour), fg='green')

    # Initialize docker client
    docker_helper = DockerHelper(local=local,
                                 log_config=invenio_cli.log_config)

    scripts_setup(local=local, force=force, stop_containers=stop_containers,
                  docker_helper=docker_helper,
                  project_shortname=invenio_cli.project_shortname,
                  log_config=invenio_cli.log_config)


@cli.command()
@click.option('--local/--containers', default=True, is_flag=True,
              help='Which environment to build, it defaults to local')
@click.option('--start/--stop', default=True, is_flag=True,
              help='Start or Stop application and services')
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def server(local, start, verbose):
    """Starts the application server."""
    # Create config object
    invenio_cli = InvenioCli(verbose=verbose)

    docker_helper = DockerHelper(local=local,
                                 log_config=invenio_cli.log_config)
    if start:
        click.secho('Booting up server...', fg='green')
        scripts_server(local=local, docker_helper=docker_helper,
                       log_config=invenio_cli.log_config)
    else:
        click.secho('Stopping server...', fg="green")
        docker_helper.stop_containers()


@cli.command()
@click.option('--local/--containers', default=True, is_flag=True,
              help='Which environment to build, it defaults to local')
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def destroy(local, verbose):
    """Removes all associated resources (containers, images, volumes)."""
    # Create config object
    invenio_cli = InvenioCli(verbose=verbose)

    click.secho('Destroying {flavour} application...'
                .format(flavour=invenio_cli.flavour), fg='green')
    docker_helper = DockerHelper(local=local,
                                 log_config=invenio_cli.log_config)
    docker_helper.destroy_containers()


@cli.command()
@click.option('--local/--containers', default=True, is_flag=True,
              help='Which environment to build, it defaults to local')
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def update(local, verbose):
    """Updates the current application static files."""
    # Create config object
    invenio_cli = InvenioCli(verbose=verbose)

    click.secho("Updating static files...", fg="green")
    if local:
        update_statics(local, log_config=invenio_cli.log_config)
        click.secho("Files updated, you might need to restart your " +
                    "application (if running)...", fg="green")
    else:
        docker_helper = DockerHelper(local=local,
                                     log_config=invenio_cli.log_config)
        update_statics(local, log_config=invenio_cli.log_config,
                       docker_helper=docker_helper,
                       project_shortname=invenio_cli.project_shortname)


@cli.command()
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def upgrade(verbose):
    """Upgrades the current application to the specified newer version."""
    # Create config object
    invenio_cli = InvenioCli(verbose=verbose)

    click.secho('Upgrading server for {flavour} application...'
                .format(flavour=invenio_cli.flavour), fg='green')
    click.secho('ERROR: Not supported yet...', fg='red')


@cli.command()
@click.option('--local/--containers', default=True, is_flag=True,
              help='Which environment to build, it defaults to local')
@click.option('--stop-containers', default=False, is_flag=True, required=False,
              help='Stop containers when finishing the setup operations.')
@click.option('--verbose', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
def demo(local, stop_containers, verbose):
    """Populates instance with demo records."""
    # Create config object
    invenio_cli = InvenioCli(verbose=verbose)
    docker_compose = DockerHelper(local=local,
                                  log_config=invenio_cli.log_config)
    populate_demo_records(local, docker_compose, invenio_cli.project_shortname,
                          invenio_cli.log_config, stop_containers)
