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
import signal
import subprocess
from configparser import ConfigParser
from pathlib import Path

import click
import docker
from cookiecutter.exceptions import OutputDirExistsException
from cookiecutter.main import cookiecutter

from .cookicutter_config import CookiecutterConfig
from .docker_compose import DockerCompose
from .filesystem import get_created_files
from .log import LogPipe

CONFIG_FILENAME = '.invenio'
CLI_SECTION = 'cli'
NAME_ITEM = 'project_name'
FLAVOUR_ITEM = 'flavour'
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
        self.name = None
        self.config = ConfigParser()
        self.config.read(CONFIG_FILENAME)
        self.verbose = verbose
        self.loglevel = loglevel

        # There is a .invenio config file
        if os.path.isfile(CONFIG_FILENAME):
            try:
                config_flavour = self.config[CLI_SECTION][FLAVOUR_ITEM]
                # Provided flavour differs from the one in .invenio
                if flavour and flavour != config_flavour:
                    logging.error('Config flavour in .invenio differs form ' +
                                  'the specified')
                    exit(1)
                # Use .invenio configured flavour
                self.flavour = config_flavour
            except KeyError:
                logging.error('Flavour not configured')
                exit(1)
            try:
                self.name = self.config[CLI_SECTION][NAME_ITEM]
            except KeyError:
                logging.error('Project name not configured')
                exit(1)
        elif flavour:
            # There is no .invenio file but the flavour was provided via CLI
            self.flavour = flavour
        else:
            # No value for flavour in .invenio nor CLI
            logging.error('No flavour specified.')
            exit(1)


@click.group()
@click.option('--flavour', type=click.Choice(['RDM'], case_sensitive=False),
              default=None, required=False)
@click.option('--log-level', required=False, default='warning',
              type=click.Choice(list(LEVELS.keys()), case_sensitive=False))
@click.option('-V', default=False, is_flag=True, required=False,
              help='Verbose mode will show all logs in the console.')
@click.pass_context
def cli(ctx, flavour, log_level, v):
    """Initialize CLI context."""
    ctx.obj = InvenioCli(
        flavour=flavour,
        loglevel=LEVELS[log_level],
        verbose=v
    )


@cli.command()
@click.pass_obj
def init(cli_obj):
    """Initializes the application according to the chosen flavour."""
    print('Initializing {flavour} application...'.format(
        flavour=cli_obj.flavour))
    cookie_config = CookiecutterConfig()

    try:
        context = cookiecutter(
            config_file=cookie_config.create_and_dump_config(),
            **cookie_config.repository(cli_obj.flavour)
        )

        config = cli_obj.config

        file_fullpath = Path(context) / CONFIG_FILENAME

        with open(file_fullpath, 'w') as configfile:
            # Open config file
            config.read(CONFIG_FILENAME)

            # CLI parameters
            config[CLI_SECTION] = {}
            config[CLI_SECTION][NAME_ITEM] = context.split(os.path.sep)[-1]
            config[CLI_SECTION][FLAVOUR_ITEM] = cli_obj.flavour
            config[COOKIECUTTER_SECTION] = {}
            # Cookiecutter user input
            replay = cookie_config.get_replay()
            for key, value in replay[COOKIECUTTER_SECTION].items():
                config[COOKIECUTTER_SECTION][key] = value
            # Generated files
            config[FILES_SECTION] = get_created_files(
                    config[COOKIECUTTER_SECTION]['project_shortname'])

            config.write(configfile)

    except OutputDirExistsException as e:
        print(str(e))

    finally:
        cookie_config.remove_config()


@cli.command()
@click.pass_obj
@click.option('--dev/--prod', default=True, is_flag=True,
              help='Which environment to build, it defaults to development')
@click.option('--base/--skip-base', default=True, is_flag=True,
              help='If specified, it will build the base docker image ' +
                   '(not compatible with --dev)')
@click.option('--app/--skip-app', default=True, is_flag=True,
              help='If specified, it will build the application docker ' +
                   'image (not compatible with --dev)')
@click.option('--pre', default=False, is_flag=True,
              help='If specified, allows the installation of alpha releases')
@click.option('--lock/--skip-lock', default=True, is_flag=True,
              help='Lock dependencies or avoid this step')
def build(cli_obj, base, app, pre, dev, lock):
    """Locks the dependencies and builds the corresponding docker images."""
    print('Building {flavour} application...'.format(flavour=cli_obj.flavour))

    # Open logging pipe
    logpipe = LogPipe(cli_obj.loglevel)
    if lock:
        # Lock dependencies
        print('Locking dependencies...')
        command = ['pipenv', 'lock']
        if pre:
            command.append('--pre')
        # No need for `with` context since call is a blocking op
        subprocess.call(command, stdout=logpipe, stderr=logpipe)

    if dev:
        # FIXME: Scripts should be changed by commands run here
        print('Bootstrapping development server...')
        subprocess.call(['/bin/bash', 'scripts/bootstrap', '--dev'],
                        stdout=logpipe, stderr=logpipe)

        print('Creating development services...')
        DockerCompose.create_images(dev=True, loglevel=cli_obj.loglevel)
    else:
        if base:
            print('Building {flavour} base docker image...'.format(
                flavour=cli_obj.flavour))
            # docker build -f Dockerfile.base -t my-site-base:latest .
            client = docker.from_env()
            client.images.build(
                dockerfile='Dockerfile.base',
                tag='{project_name}-base:latest'.format(
                    project_name=cli_obj.name)
            )
        if app:
            print('Building {flavour} app docker image...'.format(
                flavour=cli_obj.flavour))
            # docker build -t my-site:latest .
            # FIXME: Reuse client
            client = docker.from_env()
            client.images.build(
                dockerfile='Dockerfile',
                tag='{project_name}:latest'.format(
                    project_name=cli_obj.name)
            )
        print('Creating full services...')
        DockerCompose.create_images(dev=False, loglevel=cli_obj.loglevel)

    # Close logging pipe
    logpipe.close()


@cli.command()
@click.option('--dev/--prod', default=True, is_flag=True,
              help='Which environment to build, it defaults to development')
@click.pass_obj
def setup(cli_obj, dev):
    """Sets up the application for the first time (DB, ES, queue, etc.)."""
    print('Setting up environment for {flavour} application...'
          .format(flavour=cli_obj.flavour))

    # Open logging pipe
    logpipe = LogPipe(cli_obj.loglevel)
    if dev:
        # FIXME: Scripts should be changed by commands run here
        subprocess.call(['/bin/bash', 'scripts/setup', '--dev'],
                        stdout=logpipe, stderr=logpipe)
    else:
        # FIXME: Scripts should be changed by commands run here
        print('Setting up instance...')
        subprocess.call(['docker-compose', 'exec', 'web-api',
                         '/bin/bash', '-c',
                         '/bin/bash /opt/invenio/src/scripts/setup'],
                        stdout=logpipe, stderr=logpipe)

    # Close logging pipe
    logpipe.close()


@cli.command()
@click.option('--dev/--prod', default=True, is_flag=True,
              help='Which environment to build, it defaults to development')
@click.option('--bg', default=False, is_flag=True,
              help='Run the containers in foreground')
@click.option('--start/--stop', default=True, is_flag=True,
              help='Start or Stop application and services')
@click.pass_obj
def run(cli_obj, dev, bg, start):
    """Starts the application server."""
    if start:
        print('Starting server...')

        def signal_handler(sig, frame):
            print('Stopping server...')
            # Close logging pipe
            logpipe.close()
            DockerCompose.stop_containers(cli_obj.loglevel)

        signal.signal(signal.SIGINT, signal_handler)

        if dev:
            print()
            DockerCompose.start_containers(dev=True, bg=bg,
                                           loglevel=cli_obj.loglevel)

            # Open logging pipe
            logpipe = LogPipe(cli_obj.loglevel)

            # FIXME: Scripts should be changed by commands run here
            if bg:
                server = subprocess.Popen(['/bin/bash', 'scripts/server'],
                                          stdout=logpipe, stderr=logpipe)
                print('Server up and running...')
                server.wait()
            else:
                server = subprocess.call(['/bin/bash', 'scripts/server'])
        else:
            DockerCompose.start_containers(dev=False, bg=bg,
                                           loglevel=cli_obj.loglevel)

    else:
        print('Stopping server...')
        DockerCompose.stop_containers(loglevel=cli_obj.loglevel)


@cli.command()
@click.option('--dev/--prod', default=True, is_flag=True,
              help='Which environment to build, it defaults to development')
@click.pass_obj
def destroy(cli_obj, dev):
    """Removes all associated resources (containers, images, volumes)."""
    print('Destroying {flavour} application...'
          .format(flavour=cli_obj.flavour))
    DockerCompose.destroy_containers(dev=dev, loglevel=cli_obj.loglevel)


@cli.command()
@click.pass_obj
def upgrade(cli_obj):
    """Upgrades the current application to the specified newer version."""
    print('Upgrading server for {flavour} application...'
          .format(flavour=cli_obj.flavour))
    print('ERROR: Not supported yet...')
