# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Previous script files helper methods."""

import errno
import logging
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


def _bootstrap_dev(pre, loglevel, logfile, verbose):
    # Check if the dependencies have been locked, fail if not
    click.secho('Checking that dependencies are locked...', fg='green')
    locked = 'Pipfile.lock' in os.listdir('.')
    if not locked:
        click.secho('Cannot build without locked dependencies', fg='red')
        exit(1)

    # Open logging pipe
    logpipe = LogPipe(loglevel, logfile)

    # Install packages according to the lock file
    click.secho('Installing dependencies...', fg='green')
    command = ['pipenv', 'sync', '--dev']

    if pre:
        command.append('--pre')
    subprocess.call(command, stdout=logpipe, stderr=logpipe)

    # Close logging pipe
    logpipe.close()

    # Build assets
    build_assets(verbose)

    # Update static files
    update_statics(True, loglevel, logfile)

    # Update configuration
    update_config(True, loglevel, logfile)


def _boostrap_prod(base, docker_helper, project_shortname):
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


def bootstrap(dev=True, pre=True,
              base=True, docker_helper=None, project_shortname='invenio-rdm',
              verbose=False, loglevel=logging.WARN, logfile='invenio-cli.log'):
    """Bootstrap server."""
    click.secho('Bootstrapping server...', fg='green')
    if dev:
        _bootstrap_dev(pre, loglevel, logfile, verbose)
    else:
        _boostrap_prod(base, docker_helper, project_shortname)


@with_appcontext
def build_assets(verbose):
    """Build assets."""
    cli = create_cli()
    runner = current_app.test_cli_runner()
    # Collect
    run_command(cli, runner, "collect -v", message="Collecting assets...",
                verbose=verbose)

    # Build using webpack
    run_command(cli, runner, "webpack buildall",
                message="Building assets...", verbose=verbose)


def _force_symlink(file1, file2):
    try:
        os.symlink(file1, file2)
    except OSError as e:
        if e.errno == errno.EEXIST:
            os.remove(file2)
            os.symlink(file1, file2)


def update_config(dev, loglevel, logfile):
    """Update invenio.cfg configuration file."""
    if dev:
        # Create symbolic link
        dst_path = _get_instance_path(loglevel, logfile)
        src_file = os.path.abspath('invenio.cfg')
        _force_symlink(src_file, Path(dst_path) / 'invenio.cfg')

    else:
        # Copy to container
        pass


def update_statics(dev, loglevel, logfile, docker_helper=None,
                   project_shortname=None):
    """Update static files."""
    src_file = os.path.abspath('static/images/logo.svg')

    if dev:
        # Copy logo file
        dst_path = _get_instance_path(loglevel, logfile)
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


def _get_instance_path(loglevel, logfile):
    # Open logging pipe
    logpipe = LogPipe(loglevel, logfile)

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

def _setup_dev(force, cli, runner, verbose, loglevel, logfile):
    # Clean things up
    if force:
        run_command(cli, runner, 'shell --no-term-title -c ' +
                    '"import redis; redis.StrictRedis.from_url(' +
                    "app.config['CACHE_REDIS_URL']).flushall();" +
                    'print(\'Cache cleared\')"',
                    message="Flushing redis cache...", verbose=verbose)
        run_command(cli, runner, 'db destroy --yes-i-know',
                    message="Deleting database...", verbose=verbose)
        run_command(cli, runner, 'index destroy --force --yes-i-know',
                    message="Deleting indexes...", verbose=verbose)
        run_command(cli, runner, 'index queue init purge',
                    message="Purging queues...", verbose=verbose)

    run_command(cli, runner, 'db init create',
                message="Creating database...", verbose=verbose)
    run_command(cli, runner, 'index init',
                message="Creating indexes...", verbose=verbose)
    run_command(cli, runner, "files location --default 'default-location' " +
                "{})".format(_get_instance_path(loglevel, logfile)),
                message="Creating files location...", verbose=verbose)
    run_command(cli, runner, 'roles create admin',
                message="Creating admin role...", verbose=verbose)
    run_command(cli, runner, 'access allow superuser-access role admin',
                message="Assigning superuser access to admin role...",
                verbose=verbose)


def _setup_prod(force, docker_helper, project_shortname):
    # Clean things up
    if force:
        click.secho("Flushing redis cache...", fg="green")
        docker_helper.execute_cli_command(
            project_shortname,
            'invenio shell --no-term-title -c "import redis; ' +
            "redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL'])" +
            '.flushall(); print(\'Cache cleared\')"')
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
        project_shortname, 'invenio db init create',)
    click.secho("Creating indexes...", fg="green")
    docker_helper.execute_cli_command(
        project_shortname, 'invenio index init')
    click.secho("Creating files location...", fg="green")
    docker_helper.execute_cli_command(
        project_shortname,
        "invenio files location --default 'default-location'")
    click.secho("Creating admin role...", fg="green")
    docker_helper.execute_cli_command(
        project_shortname, 'invenio roles create admin')
    click.secho("Assigning superuser access to admin role...", fg="green")
    docker_helper.execute_cli_command(
        project_shortname, 'invenio access allow superuser-access role admin')


@with_appcontext
def setup(dev=True, force=False, docker_helper=None,
          project_shortname='invenio-rdm', verbose=False,
          loglevel=logging.WARN, logfile='invenio-cli.log'):
    """Bootstrap server."""
    click.secho('Setting up server...', fg='green')
    cli = create_cli()
    runner = current_app.test_cli_runner()

    click.secho("Starting containers...", fg="green")
    docker_helper.start_containers()
    time.sleep(60)  # Give time to the containers to start properly

    if dev:
        _setup_dev(force, cli, runner, verbose, loglevel, logfile)
    else:
        _setup_prod(force, docker_helper, project_shortname)

    docker_helper.stop_containers()


##########
# SERVER #
##########


def _server_dev(docker_helper, loglevel, logfile, verbose):

    def signal_handler(sig, frame):
        click.secho('Stopping server...', fg='green')
        # Stop server
        os.kill(server.pid, signal.SIGTERM)
        # Stop worker
        os.kill(worker.pid, signal.SIGTERM)
        # Stop containers
        docker_helper.stop_containers()
        time.sleep(10)  # Allow last logs to get into the file
        # Close logging pipe
        logpipe.close()
        click.secho("Server and worker stopped...", fg="green")

    signal.signal(signal.SIGINT, signal_handler)

    docker_helper.start_containers()

    # Open logging pipe
    logpipe = LogPipe(loglevel, logfile) if verbose else subprocess.PIPE

    click.secho("Starting celery worker...", fg="green")
    worker = subprocess.Popen(['pipenv', 'run', 'celery', 'worker',
                               '--app', 'invenio_app.celery'],
                              stdout=logpipe, stderr=logpipe)

    click.secho("Starting up development server...", fg='green')

    server = subprocess.Popen(['pipenv', 'run', 'invenio', 'run',
                               '--cert', 'docker/nginx/test.crt',
                               '--key', 'docker/nginx/test.key'],
                              stdout=logpipe, stderr=logpipe)

    click.secho('Server up and running...', fg='green')
    worker.wait()
    server.wait()


def server(dev=True, docker_helper=None, project_shortname='invenio-rdm',
           verbose=False, loglevel=logging.WARN, logfile='invenio-cli.log'):
    """Run server."""
    if dev:
        _server_dev(docker_helper, loglevel, logfile, verbose)
    else:
        click.secho("Starting docker containers. " +
                    "It might take up to a minute.", fg="green")
        click.secho("Use --stop to stop server.", fg="green")
        docker_helper.start_containers()
        time.sleep(60)


############
# POPULATE #
############


@with_appcontext
def populate_demo_records(dev, docker_helper, verbose, project_shortname):
    """Add demo records into the instance."""
    # FIXME: Needs to execute in docker container if "prod"
    click.secho('Setting up server...', fg='green')
    cli = create_cli()
    runner = current_app.test_cli_runner()

    click.secho("Starting containers...", fg="green")
    docker_helper.start_containers()
    time.sleep(60)  # Give time to the containers to start properly

    if dev:
        run_command(cli, runner, 'rdm-records demo',
                    message="Populating instance with demo records...",
                    verbose=verbose)
    else:
        click.secho("Populating instance with demo records...", fg="green")
        docker_helper.execute_cli_command(
            project_shortname, 'invenio rdm-records demo')

    docker_helper.stop_containers()
    time.sleep(30)
