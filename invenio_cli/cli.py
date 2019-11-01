# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University,
#                    Galter Health Sciences Library & Learning Center.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import logging
import os
import signal
import subprocess
import sys

import click
import docker
from cookiecutter.main import cookiecutter

from .utils import DockerCompose, cookiecutter_repo

# In order to have Python 2.7 lowers compatibility.
if sys.version_info[0] == 2:
    from ConfigParser import ConfigParser
else:
    from configparser import ConfigParser

CONFIG_FILENAME = '.invenio'


class InvenioCli(object):
    """Current application building properties."""

    def __init__(self, flavour=None):
        r"""Initialize builder.

        :param flavour: Flavour name.
        """
        self.cwd = None
        self.flavour = None
        self.name = None
        self.config = ConfigParser()
        self.config.read(CONFIG_FILENAME)

        # There is a .invenio config file
        if os.path.isfile(CONFIG_FILENAME):
            try:
                config_flavour = self.config['cli']['flavour']
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
                self.cwd = self.config['cli']['cwd']
                self.name = self.cwd.split('/')[-1] if self.cwd else None
            except KeyError:
                logging.debug('Working directory not configured')
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
@click.pass_context
def cli(ctx, flavour):
    """Initialize CLI context."""
    ctx.obj = InvenioCli(flavour=flavour)


@cli.command()
@click.pass_obj
def init(cli_obj):
    """Initializes the application according to the chosen flavour."""
    print('Initializing {flavour} application...'.format(
        flavour=cli_obj.flavour))
    context = cookiecutter(**cookiecutter_repo(cli_obj.flavour))
    config = cli_obj.config

    with open(CONFIG_FILENAME, 'w') as configfile:
        # Read config file
        config.read(CONFIG_FILENAME)

        if 'cli' in config.sections():
            logging.error('An invenio-cli configuration file ' +
                          '({config})'.format(config=CONFIG_FILENAME) +
                          'already exists. Cannot override')

        else:
            config['cli'] = {}
            config['cli']['cwd'] = context
            config['cli']['flavour'] = cli_obj.flavour
            config.write(configfile)


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
    if lock:
        # Lock dependencies
        print('Locking dependencies...')
        command = ['pipenv', 'lock']
        if pre:
            command.append('--pre')
        subprocess.call(command, cwd=cli_obj.cwd)

    if dev:
        # FIXME: Scripts should be changed by commands run here
        print('Bootstrapping development server...')
        subprocess.call(
            ['/bin/bash', 'scripts/bootstrap', '--dev'],
            cwd=cli_obj.cwd
        )

        print('Creating development services...')
        DockerCompose.create_containers(dev=True, cwd=cli_obj.cwd)
    else:
        if base:
            print('Building {flavour} base docker image...'.format(
                flavour=cli_obj.flavour))
            # docker build -f Dockerfile.base -t my-site-base:latest .
            client = docker.from_env()
            client.images.build(
                path=cli_obj.cwd,
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
                path=cli_obj.cwd,
                dockerfile='Dockerfile',
                tag='{project_name}:latest'.format(
                    project_name=cli_obj.name)
            )
        print('Creating full services...')
        DockerCompose.create_containers(
            dev=False,
            cwd=cli_obj.cwd
        )


@cli.command()
@click.option('--dev/--prod', default=True, is_flag=True,
              help='Which environment to build, it defaults to development')
@click.pass_obj
def setup(cli_obj, dev):
    """Sets up the application for the first time (DB, ES, queue, etc.)."""
    print('Setting up environment for {flavour} application...'
          .format(flavour=cli_obj.flavour))
    if dev:
        # FIXME: Scripts should be changed by commands run here
        subprocess.call(
            ['/bin/bash', 'scripts/setup', '--dev'],
            cwd=cli_obj.cwd
        )
    else:
        # FIXME: Scripts should be changed by commands run here
        print('Setting up instance...')
        subprocess.call(
            ['docker-compose', 'exec', 'web-api',
                '/bin/bash', '-c',
                '/bin/bash /opt/invenio/src/scripts/setup'],
            cwd=cli_obj.cwd
        )


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
    print('Starting/Stopping server for {flavour} application...'
          .format(flavour=cli_obj.flavour))
    if start:
        def signal_handler(sig, frame):
            print('SIGINT, stopping server...')
            DockerCompose.stop_containers(cwd=cli_obj.cwd)

        signal.signal(signal.SIGINT, signal_handler)

        if dev:
            # FIXME: Scripts should be changed by commands run here
            DockerCompose.start_containers(
                dev=True,
                cwd=cli_obj.cwd,
                bg=bg
            )
            # FIXME: if previous container creation is not bg it blocks
            # will never reach. Should use Popen if not bg
            # TODO: Run in background / foreground (--bg) Difficult to find
            # the process to stop. Should not be allowed?
            # FIXME: HAndle crtl+c and avoid exceptions
            subprocess.call(
                ['/bin/bash', 'scripts/server'],
                cwd=cli_obj.cwd
            )
        else:
            DockerCompose.start_containers(
                dev=False,
                cwd=cli_obj.cwd,
                bg=bg
            )

    else:
        DockerCompose.stop_containers(cwd=cli_obj.cwd)


@cli.command()
@click.option('--dev/--prod', default=True, is_flag=True,
              help='Which environment to build, it defaults to development')
@click.pass_obj
def destroy(cli_obj, dev):
    """Removes all associated resources (containers, images, volumes)."""
    print('Destroying {flavour} application...'
          .format(flavour=cli_obj.flavour))
    DockerCompose.destroy_containers(dev=dev, cwd=cli_obj.cwd)


@cli.command()
@click.pass_obj
def upgrade(cli_obj):
    """Upgrades the current application to the specified newer version."""
    print('Upgrading server for {flavour} application...'
          .format(flavour=cli_obj.flavour))
    print('ERROR: Not supported yet...')
