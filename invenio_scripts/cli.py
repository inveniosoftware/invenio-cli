# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import click
import docker
import signal
import subprocess

from cookiecutter.main import cookiecutter

from .utils import cookiecutter_repo, DockerCompose


class InvenioAppBuilder(object):
    def __init__(self, name='RDM', project_name='my-site'):
        self.name = name.upper()
        self.project_name = project_name


@click.group()
@click.option('--flavor', default='RDM',
              help='Invenio flavor. Can be RDM or ILS')
@click.option('--project-name', default='my-site',
              help='Project name as declared in cookiecutter')
@click.pass_context
def cli(ctx, flavor, project_name):
    ctx.obj = InvenioAppBuilder(name=flavor, project_name=project_name)


@cli.command()
@click.pass_obj
def init(app_builder):
    print('Initializing {flavor} application...'.format(
        flavor=app_builder.name))
    cookiecutter(**cookiecutter_repo(app_builder.name))


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
    print('Building {flavor} application...'.format(flavor=app_builder.name))
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
            print('Building {flavor} base docker image...'.format(
                flavor=app_builder.name))
            # docker build -f Dockerfile.base -t my-site-base:latest .
            client = docker.from_env()
            client.images.build(
                path=app_builder.project_name,
                dockerfile='Dockerfile.base',
                tag='{project_name}-base:latest'.format(
                    project_name=app_builder.project_name),
            )
        if app:
            print('Building {flavor} app docker image...'.format(
                flavor=app_builder.name))
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
    print('Setting up environment for {flavor} application...'
          .format(flavor=app_builder.name))
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

    print('Starting/Stopping server for {flavor} application...'
          .format(flavor=app_builder.name))
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
    print('Destroying {flavor} application...'
          .format(flavor=app_builder.name))
    DockerCompose.destroy_containers(dev=dev, cwd=app_builder.project_name)


@cli.command()
@click.pass_obj
def upgrade(app_builder):
    print('Upgrading server for {flavor} application...'
          .format(flavor=app_builder.name))
    print('ERROR: Not supported yet...')
