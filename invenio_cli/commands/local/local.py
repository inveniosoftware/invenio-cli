# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import signal
from os import environ
from subprocess import Popen as popen

import click

from ...helpers.docker_helper import DockerHelper
from ...helpers.env import env
from ...helpers.process import ProcessResponse, run_interactive
from ...helpers.services import wait_for_services
from ..commands import Commands


class LocalCommands(Commands):
    """Local environment CLI commands."""

    def __init__(self, cli_config, docker_helper=None):
        """Constructor."""
        docker_helper = docker_helper or \
            DockerHelper(cli_config.get_project_shortname(), local=True)

        super(LocalCommands, self).__init__(cli_config, docker_helper)

    def ensure_containers_running(self):
        """Ensures containers are running."""
        click.secho('Making sure containers are up...', fg='green')
        project_shortname = self.cli_config.get_project_shortname()
        docker_helper = DockerHelper(
            project_shortname,
            local=True)
        docker_helper.start_containers()

        wait_for_services(
            services=["redis", self.cli_config.get_db_type(), "es"],
            project_shortname=project_shortname,
        )

    def update_statics_and_assets(self, force, flask_env='production'):
        """High-level command to update less/js/images/... files.

        Needed here (parent) because is used by Assets and Install commands.
        """
        # Commands
        prefix = ['pipenv', 'run']
        collect_cmd = prefix + ['invenio', 'collect', '--verbose']
        clean_create_cmd = prefix + ['invenio', 'webpack', 'clean', 'create']
        create_cmd = prefix + ['invenio', 'webpack', 'create']
        install_cmd = prefix + ['invenio', 'webpack', 'install']
        build_cmd = prefix + ['invenio', 'webpack', 'build']

        with env(FLASK_ENV=flask_env):
            # Collect into statics/ and assets/ folder
            click.secho('Collecting statics and assets...', fg='green')
            run_interactive(collect_cmd)
            if force:
                run_interactive(clean_create_cmd)

                # Installs in assets/node_modules/
                click.secho('Installing JS dependencies...', fg='green')
                run_interactive(install_cmd)
            else:
                run_interactive(create_cmd)

            # Symlink the instance's statics and assets
            copied_files = self._copy_statics_and_assets()
            self._symlink_assets_templates(copied_files)

            # Build project
            click.secho('Building assets...', fg='green')
            run_interactive(build_cmd)

        # FIXME: Refactor above to make use of proper error handling.
        return ProcessResponse(
                output="Assets and statics updated.",
                status_code=0,
        )

    def run(self, host, port, debug=True, services=True):
        """Run development server and celery queue."""

        def signal_handler(sig, frame):
            click.secho('Stopping server and worker...', fg='green')
            server.terminate()
            if services:
                worker.terminate()
            click.secho("Server and worker stopped...", fg="green")

        signal.signal(signal.SIGINT, signal_handler)

        if services:
            self.ensure_containers_running()

            click.secho("Starting celery worker...", fg="green")
            worker = popen([
                'pipenv', 'run', 'celery', '--app', 'invenio_app.celery', 'worker'
            ])

        click.secho("Starting up local (development) server...", fg='green')
        run_env = environ.copy()
        run_env['FLASK_ENV'] = 'development' if debug else 'production'
        run_env['INVENIO_SITE_HOSTNAME'] = f"{host}:{port}"
        server = popen([
            'pipenv', 'run', 'invenio', 'run', '--cert',
            'docker/nginx/test.crt', '--key', 'docker/nginx/test.key',
            '--host', host, '--port', port
        ], env=run_env)

        click.secho(
            'Instance running!\nVisit https://{}:{}'.format(host, port),
            fg='green')
        server.wait()
