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
    # TODO: Make URL and branch parametrizable for each flavor
    cookiecutter(
        'https://github.com/inveniosoftware/cookiecutter-invenio-rdm.git',
        checkout='dev'
    )


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
def build(app_builder, base, app, dev):
    print('Building {flavor} application...'.format(flavor=app_builder.name))
    # TODO: Crosscheck if installed and suggest help if not
    # TODO: Check installation (add to setup.py?)
    # Lock dependencies
    print('Locking dependencies...')
    subprocess.call(['pipenv', 'lock'], cwd=app_builder.project_name)

    if dev:
        print('Bootstrapping development server...')
        subprocess.call(
            ['/bin/bash', 'scripts/bootstrap', '--dev'],
            cwd=app_builder.project_name
        )

        print('Creating development services...')
        subprocess.call(
            ['docker-compose',
                '-f', 'docker-compose.dev.yml', 'up', '--no-start'],
            cwd=app_builder.project_name
        )
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
        print('Creating services...')
        subprocess.call(
            ['docker-compose', '-f', 'docker-compose.yml', 'up', '--no-start'],
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
        # TODO: can be made in parallel (two Popen processes)
        print('Bootstrapping UI...')
        subprocess.call(
            ['docker-compose', 'exec', 'web-ui',
                '/bin/bash', '-c',
                '/bin/bash /opt/invenio/src/scripts/bootstrap'],
            cwd=app_builder.project_name
        )
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
@click.pass_obj
def server(app_builder, dev, bg):
    print('Starting server for {flavor} application...'
            .format(flavor=app_builder.name))
    # Cannot use docker-py https://github.com/docker/compose/issues/4542#issuecomment-283191533
    command = ['docker-compose',
                '-f', 'docker-compose.yml', 'up', '--no-recreate']
    if dev:
        command[2] = 'docker-compose.dev.yml'
    if bg:
        command.append('-d')
    # FIXME: It crashes since they are not stopped. Start of the non-app services
    # should happen during build time?.
    # Add --services flag
    # Different command?
    subprocess.call(
        command,
        cwd=app_builder.project_name
    )

    if dev:
        # FIXME: Scripts should be changed by commands run here
        subprocess.call(
            ['/bin/bash', 'scripts/server'],
            cwd=app_builder.project_name
        )
    else:
        # FIXME: does not get called because the command exites before
        # It does not hang with a blocking call (e.g. 'subprocess.call')
        def signal_handler(sig, frame):
            print('SIGINT, stopping server...')
            subprocess.call(
                ['docker-compose', 'stop', 'web-ui', 'web-api', 'frontend'],
                cwd=app_builder.project_name
            )

        signal.signal(signal.SIGINT, signal_handler)


@cli.command()
@click.option('--dev', default=False, is_flag=True,
                help='Application environment (dev/prod)')
@click.pass_obj
def destroy(app_builder, dev):
    print('Stopping server for {flavor} application...'
            .format(flavor=app_builder.name))
    # Cannot use docker-py https://github.com/docker/compose/issues/4542#issuecomment-283191533
    command = ['docker-compose', '-f', 'docker-compose.yml', 'down']
    if dev:
        command[2] = 'docker-compose.dev.yml'

    subprocess.call(
        command,
        cwd=app_builder.project_name
    )


@cli.command()
@click.pass_obj
def upgrade(app_builder):
    print('Upgrading server for {flavor} application...'
            .format(flavor=app_builder.name))
