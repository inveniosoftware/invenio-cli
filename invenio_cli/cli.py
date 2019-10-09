# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University,
#                    Galter Health Sciences Library & Learning Center.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

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


class InvenioCli(object):
    """Current application building properties."""

    def __init__(self, flavour='RDM'):
        r"""Initialize builder.

        :param name: Flavour name.
        :param project_name: Project name.
        """
        self.flavour = flavour.upper()
        self.config = ConfigParser()


@click.group()
@click.argument('flavour', default='RDM')
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
    config.read('{path}/invenio.cfg'.format(path=context))

    if 'cli' not in config.sections():
        config.add_section('cli')

    config.set('cli', 'cwd', context)
    config.set('cli', 'flavour', cli_obj.flavour)

    with open("{path}/invenio.cfg".format(path=context), 'w') as configfile:
        config.write(configfile)


@cli.command()
@click.pass_obj
@click.option('--base', default=False, is_flag=True,
              help='If specified, it will build the base docker image ' +
                   '(not compatible with --dev)')
@click.option('--app', default=False, is_flag=True,
              help='If specified, it will build the application docker ' +
                   'image (not compatible with --dev)')
@click.option('--dev', default=False, is_flag=True,
              help='If specified, it will build a development environment')
@click.option('--lock/--no-lock', default=True, is_flag=True,
              help='Lock dependencies or avoid this step')
def build(app_builder, base, app, dev, lock):
    """Locks the dependencies and builds the corresponding docker images."""
    print('Building {flavour} application...'.format(flavour=app_builder.name))
    if lock:
        # Lock dependencies
        print('Locking dependencies...')
        subprocess.call(['pipenv', 'lock'], cwd=app_builder.project_name)

    if dev:
        # FIXME: Scripts should be changed by commands run here
        print('Bootstrapping development server...')
        subprocess.call(
            ['/bin/bash', 'scripts/bootstrap', '--dev'],
            cwd=app_builder.project_name
        )

        print('Creating development services...')
        DockerCompose.create_containers(dev=True, cwd=app_builder.project_name)
    else:
        if base:
            print('Building {flavour} base docker image...'.format(
                flavour=app_builder.name))
            # docker build -f Dockerfile.base -t my-site-base:latest .
            client = docker.from_env()
            client.images.build(
                path=app_builder.project_name,
                dockerfile='Dockerfile.base',
                tag='{project_name}-base:latest'.format(
                    project_name=app_builder.project_name),
            )
        if app:
            print('Building {flavour} app docker image...'.format(
                flavour=app_builder.name))
            # docker build -t my-site:latest .
            # FIXME: Reuse client
            client = docker.from_env()
            client.images.build(
                path=app_builder.project_name,
                dockerfile='Dockerfile',
                tag='{project_name}:latest'.format(
                    project_name=app_builder.project_name),
            )
        print('Creating full services...')
        DockerCompose.create_containers(
            dev=False,
            cwd=app_builder.project_name
        )


@cli.command()
@click.option('--dev', default=False, is_flag=True,
              help='Application environment (dev/prod)')
@click.pass_obj
def setup(app_builder, dev):
    """Sets up the application for the first time (DB, ES, queue, etc.)."""
    print('Setting up environment for {flavour} application...'
          .format(flavour=app_builder.name))
    if dev:
        # FIXME: Scripts should be changed by commands run here
        subprocess.call(
            ['/bin/bash', 'scripts/setup', '--dev'],
            cwd=app_builder.project_name
        )
    else:
        # FIXME: Scripts should be changed by commands run here
        print('Setting up instance...')
        subprocess.call(
            ['docker-compose', 'exec', 'web-api',
                '/bin/bash', '-c',
                '/bin/bash /opt/invenio/src/scripts/setup'],
            cwd=app_builder.project_name
        )


@cli.command()
@click.option('--dev', default=False, is_flag=True,
              help='Application environment (dev/prod)')
@click.option('--bg', default=False, is_flag=True,
              help='Run the containers in foreground')
@click.option('--start/--stop', default=True, is_flag=True,
              help='Start or Stop application and services')
@click.pass_obj
def server(app_builder, dev, bg, start):
    """Starts the application server."""
    print('Starting/Stopping server for {flavour} application...'
          .format(flavour=app_builder.name))
    if start:
        def signal_handler(sig, frame):
            print('SIGINT, stopping server...')
            DockerCompose.stop_containers(cwd=app_builder.project_name)

        signal.signal(signal.SIGINT, signal_handler)

        if dev:
            # FIXME: Scripts should be changed by commands run here
            DockerCompose.start_containers(
                dev=True,
                cwd=app_builder.project_name,
                bg=bg
            )
            # FIXME: if previous container creation is not bg it blocks
            # will never reach. Should use Popen if not bg
            # TODO: Run in background / foreground (--bg) Difficult to find
            # the process to stop. Should not be allowed?
            # FIXME: HAndle crtl+c and avoid exceptions
            subprocess.call(
                ['/bin/bash', 'scripts/server'],
                cwd=app_builder.project_name
            )
        else:
            DockerCompose.start_containers(
                dev=False,
                cwd=app_builder.project_name,
                bg=bg
            )

    else:
        DockerCompose.stop_containers(cwd=app_builder.project_name)


@cli.command()
@click.option('--dev', default=False, is_flag=True,
              help='Application environment (dev/prod)')
@click.pass_obj
def destroy(app_builder, dev):
    """Removes all associated resources (containers, images, volumes)."""
    print('Destroying {flavour} application...'
          .format(flavour=app_builder.name))
    DockerCompose.destroy_containers(dev=dev, cwd=app_builder.project_name)


@cli.command()
@click.pass_obj
def upgrade(app_builder):
    """Upgrades the current application to the specified newer version."""
    print('Upgrading server for {flavour} application...'
          .format(flavour=app_builder.name))
    print('ERROR: Not supported yet...')
