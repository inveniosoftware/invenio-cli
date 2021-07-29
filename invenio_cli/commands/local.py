# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import signal
from distutils.dir_util import copy_tree
from os import environ
from pathlib import Path
from subprocess import Popen as popen

import click

from ..helpers import env, filesystem
from ..helpers.process import ProcessResponse, run_interactive
from .commands import Commands
from .services import ServicesCommands


class LocalCommands(Commands):
    """Local CLI commands."""

    def __init__(self, cli_config):
        """Constructor."""
        super(LocalCommands, self).__init__(cli_config)

    def _symlink_assets_templates(self, files_to_link):
        """Symlink the assets folder."""
        assets = 'assets'
        click.secho('Symlinking {}...'.format(assets), fg='green')

        instance_path = self.cli_config.get_instance_path()
        project_dir = self.cli_config.get_project_dir()
        for file_path in files_to_link:
            file_path = Path(file_path)
            relative_path = file_path.relative_to(instance_path)
            target_path = project_dir / relative_path
            filesystem.force_symlink(target_path, file_path)

    def _copy_statics_and_assets(self):
        """Copy project's statics and assets into instance dir."""
        click.secho('Copying project statics and assets...', fg='green')

        static = 'static'
        src_dir = self.cli_config.get_project_dir() / static
        src_dir = str(src_dir)  # copy_tree below doesn't accept Path objects
        dst_dir = self.cli_config.get_instance_path() / static
        dst_dir = str(dst_dir)
        # using it for a different purpose then intended but very useful
        copy_tree(src_dir, dst_dir)

        assets = 'assets'
        src_dir = self.cli_config.get_project_dir() / assets
        src_dir = str(src_dir)
        dst_dir = self.cli_config.get_instance_path() / assets
        dst_dir = str(dst_dir)
        # The full path to the files that were copied is returned
        copied_files = copy_tree(src_dir, dst_dir)
        return copied_files

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
            run_interactive(collect_cmd, env={'PIPENV_VERBOSITY': "-1"})
            if force:
                run_interactive(
                    clean_create_cmd, env={'PIPENV_VERBOSITY': "-1"})

                # Installs in assets/node_modules/
                click.secho('Installing JS dependencies...', fg='green')
                run_interactive(install_cmd, env={'PIPENV_VERBOSITY': "-1"})
            else:
                run_interactive(create_cmd, env={'PIPENV_VERBOSITY': "-1"})

            # Symlink the instance's statics and assets
            copied_files = self._copy_statics_and_assets()
            self._symlink_assets_templates(copied_files)

            # Build project
            click.secho('Building assets...', fg='green')
            run_interactive(build_cmd, env={'PIPENV_VERBOSITY': "-1"})

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
            ServicesCommands(self.cli_config).ensure_containers_running()

            click.secho("Starting celery worker...", fg="green")
            worker = popen([
                'pipenv', 'run', 'celery', '--app',
                'invenio_app.celery', 'worker', '--beat', '--events',
                '--loglevel', 'INFO'
            ])

        click.secho("Starting up local (development) server...", fg='green')
        run_env = environ.copy()
        run_env['FLASK_ENV'] = 'development' if debug else 'production'
        run_env['INVENIO_SITE_UI_URL'] = f"https://{host}:{port}"
        run_env['INVENIO_SITE_API_URL'] = f"https://{host}:{port}/api"
        server = popen([
            'pipenv', 'run', 'invenio', 'run', '--cert',
            'docker/nginx/test.crt', '--key', 'docker/nginx/test.key',
            '--host', host, '--port', port
        ], env=run_env)

        click.secho(
            f'Instance running!\nVisit https://{host}:{port}',
            fg='green')
        server.wait()
