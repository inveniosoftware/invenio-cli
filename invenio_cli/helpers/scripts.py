# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Previous script files helper methods."""

import errno
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_base.app import create_cli

from .log import LogPipe


def run_command(cli, runner, command, message=None, catch_exceptions=False,
                verbose=False):
    """Run [invenio] command."""
    click.secho("{}...".format(message if message else command),
                fg="green")
    res = runner.invoke(cli, command, catch_exceptions=catch_exceptions)
    if verbose:
        click.secho(res.output)


#############
# BOOTSTRAP #
#############


def _bootstrap_local(pre, log_config):
    # Check if the dependencies have been locked, fail if not
    click.secho('Checking that dependencies are locked...', fg='green')
    locked = 'Pipfile.lock' in os.listdir('.')
    if not locked:
        click.secho('Cannot build without locked dependencies', fg='red')
        exit(1)

    # Open logging pipe
    logpipe = LogPipe(log_config)

    # Install packages according to the lock file
    click.secho('Installing dependencies...', fg='green')
    command = ['pipenv', 'sync', '--dev']

    if pre:
        command.append('--pre')
    subprocess.call(command, stdout=logpipe, stderr=logpipe)

    # Close logging pipe
    logpipe.close()

    # Build assets
    _build_local_assets(log_config)

    # Update static files
    update_statics(True, log_config)

    # Update configuration
    update_config(True, log_config)


def _boostrap_containers(base, docker_helper, project_shortname):
    if base:
        click.secho('Building base docker image...', fg='green')
        # docker build -f Dockerfile.base -t my-site-base:latest .
        docker_helper.build_image(
            dockerfile='Dockerfile.base',
            tag='{project_shortname}-base:latest'.format(
                project_shortname=project_shortname)
        )

    click.secho('Building applications docker image...', fg='green')
    # docker build -t my-site:latest .
    docker_helper.build_image(
        dockerfile='Dockerfile',
        tag='{project_shortname}:latest'.format(
            project_shortname=project_shortname)
    )


def bootstrap(log_config, local=True, pre=True,
              base=True, docker_helper=None, project_shortname='invenio-rdm'):
    """Bootstrap server."""
    click.secho('Bootstrapping server...', fg='green')
    if local:
        _bootstrap_local(pre, log_config)
    else:
        _boostrap_containers(base, docker_helper, project_shortname)


@with_appcontext
def _build_local_assets(log_config, statics=True, webpack=True):
    """Build assets in the containers."""
    cli = create_cli()
    runner = current_app.test_cli_runner()
    if statics:
        # Collect
        run_command(cli, runner, "collect -v", message="Collecting assets...",
                    verbose=log_config.verbose)
    if webpack:
        # Build using webpack
        run_command(cli, runner, "webpack buildall",
                    message="Building assets...", verbose=log_config.verbose)


def _build_container_assets(log_config, statics=True, webpack=True):
    """Build assets in the containers."""
    # TODO: Check how to address this. Requires uwsgi restart.
    click.secho("Command not supported: In order to rebuild assets in the " +
                "containers environment, use the `build` command.", fg="red")
    pass


def build_assets(local, statics, webpack, log_config):
    """Build assets in the containers."""
    if local:
        _build_local_assets(log_config, statics, webpack)
    else:
        _build_container_assets(log_config, statics, webpack)


def _force_symlink(file1, file2):
    try:
        os.symlink(file1, file2)
    except OSError as e:
        if e.errno == errno.EEXIST:
            os.remove(file2)
            os.symlink(file1, file2)


def update_config(local, log_config):
    """Update invenio.cfg configuration file."""
    if local:
        # Create symbolic link
        dst_path = _get_instance_path(log_config)
        src_file = os.path.abspath('invenio.cfg')
        _force_symlink(src_file, Path(dst_path) / 'invenio.cfg')

    else:
        # Copy to container
        pass


def update_statics(local, log_config, docker_helper=None,
                   project_shortname=None):
    """Update static files."""
    src_file = os.path.abspath('static/images/logo.svg')

    if local:
        # Copy logo file
        dst_path = _get_instance_path(log_config)
        dst_path = Path(dst_path) / 'static/images'
        src_file = os.path.abspath('static/images/logo.svg')
        click.secho("Creating statics folder...", fg="green")
        try:
            os.makedirs(dst_path)  # Create directories if doesnt exist
        except FileExistsError:
            click.secho("Statics directory already exsits...", fg="yellow")

        shutil.copyfile(src_file, dst_path / 'logo.svg')

    else:
        # dst_path is a path inside the container.
        dst_path = '/opt/invenio/var/instance/static/images'
        docker_helper.copy(src_file, dst_path, project_shortname)


def _get_instance_path(log_config):
    # Open logging pipe
    logpipe = LogPipe(log_config)

    calculate_path = subprocess.Popen(
        ['pipenv', 'run', 'invenio', 'shell', '--no-term-title',
            '-c', '"print(app.instance_path, end=\'\')"'],
        stdout=subprocess.PIPE,
        stderr=logpipe)

    dst_path = calculate_path.communicate()[0]
    # Remove \n incoming with bytes sequence
    dst_path = dst_path.decode("utf-8")

    if not os.path.isdir(dst_path):
        click.secho('Could not update config. Env dir {} does not extis.'
                    .format(dst_path), fg='red')
        # Close logging pipe
        logpipe.close()
        exit(1)

    # Close logging pipe
    logpipe.close()

    return dst_path


#########
# SETUP #
#########

def _setup_local(force, cli, runner, log_config):
    # Clean things up
    if force:
        run_command(cli, runner, "shell --no-term-title -c " +
                    "\"import redis; redis.StrictRedis.from_url(" +
                    "app.config['CACHE_REDIS_URL']).flushall(); " +
                    "print('Cache cleared')\"",
                    message="Flushing redis cache...",
                    verbose=log_config.verbose)
        run_command(cli, runner, 'db destroy --yes-i-know',
                    message="Deleting database...",
                    verbose=log_config.verbose)
        run_command(cli, runner, 'index destroy --force --yes-i-know',
                    message="Deleting indexes...",
                    verbose=log_config.verbose)
        run_command(cli, runner, 'index queue init purge',
                    message="Purging queues...",
                    verbose=log_config.verbose)

    run_command(cli, runner, 'db init create',
                message="Creating database...",
                verbose=log_config.verbose)
    run_command(cli, runner, 'index init',
                message="Creating indexes...",
                verbose=log_config.verbose)
    run_command(cli, runner, "files location --default 'default-location' " +
                "{}/data".format(_get_instance_path(log_config)),
                message="Creating files location...",
                verbose=log_config.verbose)
    run_command(cli, runner, 'roles create admin',
                message="Creating admin role...",
                verbose=log_config.verbose)
    run_command(cli, runner, 'access allow superuser-access role admin',
                message="Assigning superuser access to admin role...",
                verbose=log_config.verbose)


def _setup_containers(force, docker_helper, project_shortname, log_config):
    # Clean things up
    if force:
        click.secho("Flushing redis cache...", fg="green")
        docker_helper.execute_cli_command(
            project_shortname,
            "invenio shell --no-term-title -c " +
            "\"import redis; redis.StrictRedis.from_url(" +
            "app.config['CACHE_REDIS_URL']).flushall(); " +
            "print('Cache cleared')\"")
        click.secho("Deleting database...", fg="green")
        docker_helper.execute_cli_command(
            project_shortname, 'invenio db destroy --yes-i-know')
        click.secho("Deleting indexes...", fg="green")
        docker_helper.execute_cli_command(
            project_shortname, 'invenio index destroy --force --yes-i-know')
        click.secho("Purging queues...", fg="green")
        docker_helper.execute_cli_command(
            project_shortname, 'invenio index queue init purge')

    click.secho("Creating database...", fg="green")
    docker_helper.execute_cli_command(
        project_shortname, 'invenio db init create')
    click.secho("Creating indexes...", fg="green")
    docker_helper.execute_cli_command(
        project_shortname, 'invenio index init')
    click.secho("Creating files location...", fg="green")
    docker_helper.execute_cli_command(
        project_shortname,
        "invenio files location --default 'default-location' " +
        r"${INVENIO_INSTANCE_PATH}/data")
    click.secho("Creating admin role...", fg="green")
    docker_helper.execute_cli_command(
        project_shortname, 'invenio roles create admin')
    click.secho("Assigning superuser access to admin role...", fg="green")
    docker_helper.execute_cli_command(
        project_shortname, 'invenio access allow superuser-access role admin')


@with_appcontext
def setup(log_config, local=True, force=False, docker_helper=None,
          project_shortname='invenio-rdm'):
    """Bootstrap server."""
    click.secho('Setting up server...', fg='green')

    click.secho("Starting containers...", fg="green")
    docker_helper.start_containers()
    time.sleep(60)  # Give time to the containers to start properly

    if local:
        cli = create_cli()
        runner = current_app.test_cli_runner()
        _setup_local(force, cli, runner, log_config)
    else:
        _setup_containers(force, docker_helper, project_shortname, log_config)

    click.secho("Stopping containers...", fg="green")
    docker_helper.stop_containers()
    time.sleep(30)


##########
# SERVER #
##########


def _server_local(docker_helper, log_config):

    def signal_handler(sig, frame):
        click.secho('Stopping server...', fg='green')
        # Stop server
        os.kill(server.pid, signal.SIGTERM)
        # Stop worker
        os.kill(worker.pid, signal.SIGTERM)
        # Stop containers
        docker_helper.stop_containers()
        time.sleep(30)  # Allow last logs to get into the file
        # Close logging pipe
        logpipe.close()
        click.secho("Server and worker stopped...", fg="green")

    signal.signal(signal.SIGINT, signal_handler)

    docker_helper.start_containers()

    # Open logging pipe
    logpipe = subprocess.PIPE if log_config.verbose else LogPipe(log_config)

    click.secho("Starting celery worker...", fg="green")
    worker = subprocess.Popen(['pipenv', 'run', 'celery', 'worker',
                               '--app', 'invenio_app.celery'],
                              stdout=logpipe, stderr=logpipe)

    click.secho("Starting up local (development) server...", fg='green')

    server = subprocess.Popen(['pipenv', 'run', 'invenio', 'run',
                               '--cert', 'docker/nginx/test.crt',
                               '--key', 'docker/nginx/test.key'],
                              stdout=logpipe, stderr=logpipe)

    click.secho('Server up and running...', fg='green')
    worker.wait()
    server.wait()


def server(log_config, local=True, docker_helper=None,
           project_shortname='invenio-rdm'):
    """Run server."""
    if local:
        _server_local(docker_helper, log_config)
    else:
        click.secho("Starting docker containers. " +
                    "It might take up to a minute.", fg="green")
        docker_helper.start_containers()
        click.secho("Containers started use --stop to stop server.",
                    fg="green")
        time.sleep(60)


############
# POPULATE #
############


@with_appcontext
def populate_demo_records(local, docker_helper, project_shortname, log_config):
    """Add demo records into the instance."""
    click.secho('Setting up server...', fg='green')
    cli = create_cli()
    runner = current_app.test_cli_runner()

    click.secho("Starting containers...", fg="green")
    docker_helper.start_containers()
    time.sleep(60)  # Give time to the containers to start properly

    if local:
        run_command(cli, runner, 'rdm-records demo',
                    message="Populating instance with demo records...",
                    verbose=log_config.verbose)
    else:
        click.secho("Populating instance with demo records...", fg="green")
        docker_helper.execute_cli_command(project_shortname,
                                          'invenio rdm-records demo')

    docker_helper.stop_containers()
    time.sleep(30)
