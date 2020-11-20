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
from pathlib import Path, PurePath
from subprocess import PIPE, CalledProcessError
from subprocess import Popen as popen
from subprocess import run as run_proc

import click
from pynpm import NPMPackage

from ..helpers import filesystem
from ..helpers.docker_helper import DockerHelper
from ..helpers.env import env
from ..helpers.services import wait_for_services
from .commands import Commands


class LocalCommands(Commands):
    """Local environment CLI commands."""

    def __init__(self, cli_config, docker_helper=None):
        """Constructor."""
        docker_helper = docker_helper or \
            DockerHelper(cli_config.get_project_shortname(), local=True)

        super(LocalCommands, self).__init__(cli_config, docker_helper)

    def _install_py_dependencies(self, pre, lock):
        """Install Python dependencies."""
        click.secho('Installing python dependencies...', fg='green')
        command = ['pipenv', 'install', '--dev']
        if pre:
            command += ['--pre']
        if not lock:
            command += ['--skip-lock']
        run_proc(command, check=True)

    def install_modules(self, modules):
        """Install modules."""
        if len(modules) < 1:
            raise click.UsageError("You must specify at least one module.")

        cmd = ['pipenv', 'run', 'pip', 'install']
        for m in modules:
            cmd.append('-e')
            cmd.append(m)

        try:
            run_proc(cmd, check=True)
        except CalledProcessError:
            click.secho('You must specify a valid path.', fg='red')

    def _update_instance_path(self):
        """Update path to instance in config."""
        path = run_proc(
            ['pipenv', 'run', 'invenio', 'shell', '--no-term-title',
                '-c', '"print(app.instance_path, end=\'\')"'],
            check=True, universal_newlines=True, stdout=PIPE
        ).stdout.strip()
        self.cli_config.update_instance_path(path)

    def _symlink_project_file_or_folder(self, target):
        """Create symlink in instance pointing to project file or folder."""
        click.secho('Symlinking {}...'.format(target), fg='green')
        target_path = self.cli_config.get_project_dir() / target
        link_path = self.cli_config.get_instance_path() / target
        filesystem.force_symlink(target_path, link_path)

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
        """High-level command to update less/js/images/... files."""
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
            run_proc(collect_cmd, check=True)
            if force:
                run_proc(clean_create_cmd, check=True)

                # Installs in assets/node_modules/
                click.secho('Installing JS dependencies...', fg='green')
                run_proc(install_cmd, check=True)
            else:
                run_proc(create_cmd, check=True)

            # Symlink the instance's statics and assets
            copied_files = self._copy_statics_and_assets()
            self._symlink_assets_templates(copied_files)

            # Build project
            click.secho('Building assets...', fg='green')
            run_proc(build_cmd, check=True)

    def watch_assets(self):
        """High-level command to watch assets for changes."""
        # Commands
        prefix = ['pipenv', 'run']
        watch_cmd = prefix + ['invenio', 'webpack', 'run', 'start']

        with env(FLASK_ENV='development'):
            # Collect into statics/ and assets/ folder
            click.secho('Starting assets watching (press CTRL+C to stop)...',
                        fg='green')
            run_proc(watch_cmd, check=True)

    @staticmethod
    def _watch_js_module(pkg):
        """Watch the JS module for changes."""
        click.secho('Starting watching module...', fg='green')
        pkg.run_script('watch')

    @staticmethod
    def _module_pkg(path):
        """NPM package for the given path."""
        return NPMPackage(Path(path) / 'package.json')

    def _assets_pkg(self):
        """NPM package for the instance's webpack project."""
        return self._module_pkg(self.cli_config.get_instance_path() / 'assets')

    def link_js_module(self, path):
        """High-level command to install and build a JS module."""
        module_pkg = self._module_pkg(path)
        assets_pkg = self._assets_pkg()

        # Create link to global folder
        click.secho('Linking module...', fg='green')
        module_pkg.run_script('link-dist')

        # Link the global folder to the assets folder.
        assets_pkg.link(module_pkg.package_json['name'])

    def watch_js_module(self, path, link=True):
        """High-level command to watch a JS module for changes."""
        if link:
            self.link_js_module(path)

        click.secho('Starting watching module...', fg='green')
        self._module_pkg(path).run_script('watch')

    def install(self, pre, lock, flask_env='production'):
        """Local build."""
        self._install_py_dependencies(pre, lock)
        self._update_instance_path()
        self._symlink_project_file_or_folder('invenio.cfg')
        self._symlink_project_file_or_folder('templates')
        self._symlink_project_file_or_folder('app_data')
        self.update_statics_and_assets(force=True, flask_env=flask_env)

    def _ensure_containers_running(self):
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

    def services(self, force):
        """Local start of containers (services).

        NOTE: We use check=True to mimic set -e from original setup script
              i.e. if a command fails, an exception is raised

        A check in invenio-cli's config file is done to see if one-time setup
        has been executed before.
        """
        self._ensure_containers_running()

        if force:
            command = [
                'pipenv', 'run', 'invenio', 'shell', '--no-term-title', '-c',
                "import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')"  # noqa
            ]
            run_proc(command, check=True)

            # TODO: invenio-db#126 should make it idempotent
            command = [
                'pipenv', 'run', 'invenio', 'db', 'destroy', '--yes-i-know',
            ]
            run_proc(command, check=True)

            # TODO: invenio-indexer#114 should make destroy and queue init
            #       purge idempotent
            command = [
                'pipenv', 'run', 'invenio', 'index', 'destroy',
                '--force', '--yes-i-know',
            ]
            run_proc(command, check=True)

            command = [
                'pipenv', 'run', 'invenio', 'index', 'queue', 'init', 'purge']
            run_proc(command, check=True)

            self.cli_config.update_services_setup(False)

        if not self.cli_config.get_services_setup():
            command = ['pipenv', 'run', 'invenio', 'db', 'init', 'create']
            run_proc(command, check=True)

            command = [
                'pipenv', 'run', 'invenio', 'files', 'location', 'create',
                '--default', 'default-location',
                "{}/data".format(self.cli_config.get_instance_path())
            ]
            run_proc(command, check=True)

            # Without the self.cli_config.get_services_setup() check
            # this throws an error on re-runs
            # TODO: invenio-accounts#297 should make it idempotent
            command = ['pipenv', 'run', 'invenio', 'roles', 'create', 'admin']
            run_proc(command, check=True)

            command = [
                'pipenv', 'run', 'invenio', 'access', 'allow',
                'superuser-access', 'role', 'admin'
            ]
            run_proc(command, check=True)

            # Without the self.cli_config.get_services_setup() check
            # this throws an error on re-runs
            # TODO: invenio-indexer#115 should make it idempotent
            command = ['pipenv', 'run', 'invenio', 'index', 'init']
            run_proc(command, check=True)

            self.cli_config.update_services_setup(True)

    def demo(self):
        """Add demo records into the instance."""
        self._ensure_containers_running()

        command = ['pipenv', 'run', 'invenio', 'rdm-records', 'demo']
        run_proc(command, check=True)

    def run(self, host, port, debug):
        """Run development server and celery queue."""
        self._ensure_containers_running()

        def signal_handler(sig, frame):
            click.secho('Stopping server and worker...', fg='green')
            server.terminate()
            worker.terminate()
            click.secho("Server and worker stopped...", fg="green")

        signal.signal(signal.SIGINT, signal_handler)

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
