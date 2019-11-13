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
from cookiecutter.exceptions import OutputDirExistsException
from cookiecutter.main import cookiecutter

from .cookicutter_config import CookiecutterConfig
from .docker_compose import DockerCompose
from .filesystem import get_created_files
from .log import LogPipe

CONFIG_FILENAME = '.invenio'
CLI_SECTION = 'cli'
# NOTE: If modifying the list check the impact int he `init` command.
CLI_ITEMS = ['project_name', 'flavour', 'logifle']
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
        r"""Initialize builder.

        :param flavour: Flavour name.
        """
        self.flavour = None
        self.name = None
        self.config = ConfigParser()
        self.config.read(CONFIG_FILENAME)
        self.verbose = verbose
        self.loglevel = loglevel
        self.logfile = None

        # There is a .invenio config file
        if os.path.isfile(CONFIG_FILENAME):
            try:
                for item in CLI_ITEMS:
                    setattr(self, CLI_ITEMS, self.config[CLI_SECTION][item])
            except KeyError:
                logging.error(
                    '{item} not configured in CLI section'.format(item=item))
                exit(1)
            # Provided flavour differs from the one in .invenio
            if flavour and flavour != self.flavour:
                logging.error('Config flavour in .invenio differs form ' +
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
@click.option('--flavour', type=click.Choice(['RDM'], case_sensitive=False),
              default=None, required=False)
@click.option('--log-level', required=False, default='warning',
              type=click.Choice(list(LEVELS.keys()), case_sensitive=False))
@click.option('-V', default=False, is_flag=True, required=False,
              help='Verbose mode, puts the application in debug mode on the \
                  terminal output.')
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
            config[CLI_SECTION]['flavour'] = cli_obj.flavour
            config[CLI_SECTION]['project_name'] = \
                context.split(os.path.sep)[-1]
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
    logpipe = LogPipe(cli_obj.loglevel, cli_obj.logfile)
    # Initialize docker client
    docker_compose = DockerCompose(dev=dev, loglevel=cli_obj.loglevel,
                                   logfile=cli_obj.logfile)
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

    else:
        if base:
            print('Building {flavour} base docker image...'.format(
                flavour=cli_obj.flavour))
            # docker build -f Dockerfile.base -t my-site-base:latest .
            docker_compose.built_image(
                dockerfile='Dockerfile.base',
                tag='{project_name}-base:latest'.format(
                    project_name=cli_obj.name)
            )
        if app:
            print('Building {flavour} app docker image...'.format(
                flavour=cli_obj.flavour))
            # docker build -t my-site:latest .
            docker_compose.built_image(
                dockerfile='Dockerfile',
                tag='{project_name}:latest'.format(
                    project_name=cli_obj.name)
            )

        print('Creating {mode} services...'.format(
                        mode='development' if dev else 'semi-production'))
        docker_compose.create_images()

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
    logpipe = LogPipe(cli_obj.loglevel, cli_obj.logfile)
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
@click.option('--bg', default=True, is_flag=True,
              help='Run the containers in foreground')
@click.option('--start/--stop', default=True, is_flag=True,
              help='Start or Stop application and services')
@click.pass_obj
def run(cli_obj, dev, bg, start):
    """Starts the application server."""
    docker_compose = DockerCompose(dev=dev, bg=bg, logfile=cli_obj.logfile,
                                   loglevel=cli_obj.loglevel)
    if start:
        print('Starting server...')

        def signal_handler(sig, frame):
            print('Stopping server...')
            # Close logging pipe
            logpipe.close()
            docker_compose.stop_containers()

        signal.signal(signal.SIGINT, signal_handler)

        docker_compose.start_containers()
        if dev:
            # Open logging pipe
            logpipe = LogPipe(cli_obj.loglevel, cli_obj.logfile)

            # FIXME: Scripts should be changed by commands run here
            if bg:
                server = subprocess.Popen(['/bin/bash', 'scripts/server'],
                                          stdout=logpipe, stderr=logpipe)
                print('Server up and running...')
                server.wait()
            else:
                server = subprocess.call(['/bin/bash', 'scripts/server'])

    else:
        print('Starting server...')
        docker_compose.stop_containers()


@cli.command()
@click.option('--dev/--prod', default=True, is_flag=True,
              help='Which environment to build, it defaults to development')
@click.pass_obj
def destroy(cli_obj, dev):
    """Removes all associated resources (containers, images, volumes)."""
    print('Destroying {flavour} application...'
          .format(flavour=cli_obj.flavour))
    docker_compose = DockerCompose(dev=dev, loglevel=cli_obj.loglevel,
                                   logfile=cli_obj.logfile)
    docker_compose.destroy_containers()


@cli.command()
@click.pass_obj
def upgrade(cli_obj):
    """Upgrades the current application to the specified newer version."""
    print('Upgrading server for {flavour} application...'
          .format(flavour=cli_obj.flavour))
    print('ERROR: Not supported yet...')
