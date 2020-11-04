# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Local and Containerized Commands."""

import os
import signal
import subprocess
import time
from distutils import dir_util
from pathlib import Path

import click
from pynpm import NPMPackage

from . import filesystem
from .docker_helper import DockerHelper
from .env import env


class Commands(object):
    """Abstraction over CLI commands that are either local or containerized."""

    def __init__(self, cli_config, local):
        """Constructor.

        :param cli_config: :class:CLIConfig instance
        :param local: boolean True if local environment
        """
        if local:
            self.environment = LocalCommands(cli_config)
        else:
            self.environment = ContainerizedCommands(
                cli_config,
                DockerHelper(
                    project_shortname=cli_config.get_project_shortname(),
                    local=False)
            )

    def __getattr__(self, name):
        """Delegate commands according to environment."""
        return getattr(self.environment, name)


class LocalCommands(object):
    """Local environment CLI commands."""

    def __init__(self, cli_config):
        """Constructor."""
        self.cli_config = cli_config

    def _install_py_dependencies(self, pre, lock):
        """Install Python dependencies."""
        click.secho('Installing python dependencies...', fg='green')
        command = ['pipenv', 'install', '--dev']
        if pre:
            command += ['--pre']
        if not lock:
            command += ['--skip-lock']
        subprocess.run(command, check=True)

    def _update_instance_path(self):
        """Update path to instance in config."""
        path = subprocess.run(
            ['pipenv', 'run', 'invenio', 'shell', '--no-term-title',
                '-c', '"print(app.instance_path, end=\'\')"'],
            check=True, universal_newlines=True, stdout=subprocess.PIPE
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

        instance_path = str(self.cli_config.get_instance_path()) + '/'
        project_dir = str(self.cli_config.get_project_dir())
        for file_path in files_to_link:
            relpath = file_path.split(instance_path)[1]
            target_path = os.path.join(project_dir, relpath)
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
        dir_util.copy_tree(src_dir, dst_dir)

        assets = 'assets'
        src_dir = self.cli_config.get_project_dir() / assets
        src_dir = str(src_dir)
        dst_dir = self.cli_config.get_instance_path() / assets
        dst_dir = str(dst_dir)
        # The full path to the files that were copied is returned
        copied_files = dir_util.copy_tree(src_dir, dst_dir)
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
            subprocess.run(collect_cmd, check=True)
            if force:
                subprocess.run(clean_create_cmd, check=True)

                # Installs in assets/node_modules/
                click.secho('Installing JS dependencies...', fg='green')
                subprocess.run(install_cmd, check=True)
            else:
                subprocess.run(create_cmd, check=True)

            # Symlink the instance's statics and assets
            copied_files = self._copy_statics_and_assets()
            self._symlink_assets_templates(copied_files)

            # Build project
            click.secho('Building assets...', fg='green')
            subprocess.run(build_cmd, check=True)

    def watch_assets(self):
        """High-level command to watch assets for changes."""
        # Commands
        prefix = ['pipenv', 'run']
        watch_cmd = prefix + ['invenio', 'webpack', 'run', 'start']

        with env(FLASK_ENV='development'):
            # Collect into statics/ and assets/ folder
            click.secho('Starting assets watching (press CTRL+C to stop)...',
                        fg='green')
            subprocess.run(watch_cmd, check=True)

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
        docker_helper = DockerHelper(
            self.cli_config.get_project_shortname(),
            local=True)
        docker_helper.start_containers()
        # TODO: Find faster way to procede when containers are ready
        time.sleep(30)  # Give time to the containers to start properly

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
            subprocess.run(command, check=True)

            # TODO: invenio-db#126 should make it idempotent
            command = [
                'pipenv', 'run', 'invenio', 'db', 'destroy', '--yes-i-know',
            ]
            subprocess.run(command, check=True)

            # TODO: invenio-indexer#114 should make destroy and queue init
            #       purge idempotent
            command = [
                'pipenv', 'run', 'invenio', 'index', 'destroy',
                '--force', '--yes-i-know',
            ]
            subprocess.run(command, check=True)

            command = [
                'pipenv', 'run', 'invenio', 'index', 'queue', 'init', 'purge']
            subprocess.run(command, check=True)

            self.cli_config.update_services_setup(False)

        if not self.cli_config.get_services_setup():
            command = ['pipenv', 'run', 'invenio', 'db', 'init', 'create']
            subprocess.run(command, check=True)

            command = [
                'pipenv', 'run', 'invenio', 'files', 'location', 'create',
                '--default', 'default-location',
                "{}/data".format(self.cli_config.get_instance_path())
            ]
            subprocess.run(command, check=True)

            # Without the self.cli_config.get_services_setup() check
            # this throws an error on re-runs
            # TODO: invenio-accounts#297 should make it idempotent
            command = ['pipenv', 'run', 'invenio', 'roles', 'create', 'admin']
            subprocess.run(command, check=True)

            command = [
                'pipenv', 'run', 'invenio', 'access', 'allow',
                'superuser-access', 'role', 'admin'
            ]
            subprocess.run(command, check=True)

            # Without the self.cli_config.get_services_setup() check
            # this throws an error on re-runs
            # TODO: invenio-indexer#115 should make it idempotent
            command = ['pipenv', 'run', 'invenio', 'index', 'init']
            subprocess.run(command, check=True)

            self.cli_config.update_services_setup(True)

    def demo(self):
        """Add demo records into the instance."""
        self._ensure_containers_running()

        command = ['pipenv', 'run', 'invenio', 'rdm-records', 'demo']
        subprocess.run(command, check=True)

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
        worker = subprocess.Popen([
            'pipenv', 'run', 'celery', '--app', 'invenio_app.celery', 'worker'
        ])

        click.secho("Starting up local (development) server...", fg='green')
        run_env = os.environ.copy()
        run_env['FLASK_ENV'] = 'development' if debug else 'production'
        run_env['INVENIO_SITE_HOSTNAME'] = f"{host}:{port}"
        server = subprocess.Popen([
            'pipenv', 'run', 'invenio', 'run', '--cert',
            'docker/nginx/test.crt', '--key', 'docker/nginx/test.key',
            '--host', host, '--port', port
        ], env=run_env)

        click.secho(
            'Instance running!\nVisit https://{}:{}'.format(host, port),
            fg='green')
        server.wait()

    def shell(self):
        """Start a shell in the virtual environment."""
        command = ['pipenv', 'shell', ]
        subprocess.run(command, check=True)

    def pyshell(self, debug=False):
        """Start a Python shell."""
        with env(FLASK_ENV='development' if debug else 'production'):
            command = ['pipenv', 'run', 'invenio', 'shell']
            subprocess.run(command, check=True)


class ContainerizedCommands(object):
    """Containerized environment CLI commands."""

    def __init__(self, cli_config, docker_helper):
        """Constructor."""
        self.cli_config = cli_config
        self.docker_helper = docker_helper

    def update_statics_and_assets(self, install):
        """Update application containers' statics and assets."""
        project_shortname = self.cli_config.get_project_shortname()

        click.secho('Collecting statics and assets...', fg='green')
        # Collect into statics/ folder
        self.docker_helper.execute_cli_command(
            project_shortname, 'invenio collect')

        # Collect into assets/ folder
        self.docker_helper.execute_cli_command(
            project_shortname, 'invenio webpack create')

        if install:
            click.secho('Installing js dependencies...', fg='green')
            # Installs in assets/node_modules/
            self.docker_helper.execute_cli_command(
                project_shortname, 'invenio webpack install --unsafe')

        # Use the copy approach rather than the symlink one in container
        click.secho('Copying project statics and assets...', fg='green')
        src_dir = self.cli_config.get_project_dir() / 'static'
        # src_dir MUST be '<dir>/.' for docker cp to work
        src_dir = os.path.join(src_dir, '.')
        dst_dir = '/opt/invenio/var/instance/static/'
        self.docker_helper.copy2(src_dir, dst_dir)

        src_dir = self.cli_config.get_project_dir() / 'assets'
        # src_dir MUST be '<dir>/.' for docker cp to work
        src_dir = os.path.join(src_dir, '.')
        dst_dir = '/opt/invenio/var/instance/assets/'
        self.docker_helper.copy2(src_dir, dst_dir)

        click.secho('Building assets...', fg='green')
        self.docker_helper.execute_cli_command(
            project_shortname, 'invenio webpack build')

    def _lock_python_dependencies(self, pre):
        """Creates Pipfile.lock if not existing."""
        command = ['pipenv', 'lock']

        if pre:
            command += ['--pre']

        locked = 'Pipfile.lock' in os.listdir('.')
        if not locked:
            subprocess.run(command, check=True)

    def containerize(self, pre, force, install):
        """Launch fully containerized application."""
        self._lock_python_dependencies(pre)

        click.secho('Making sure containers are up...', fg='green')
        self.docker_helper.start_containers()
        # TODO: Find faster way to procede when containers are ready
        time.sleep(30)  # Give time to the containers to start properly

        project_shortname = self.cli_config.get_project_shortname()

        if force:
            self.cli_config.update_services_setup(False)
            click.secho("Flushing redis cache...", fg="green")
            self.docker_helper.execute_cli_command(
                project_shortname,
                "invenio shell --no-term-title -c "
                "\"import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')\""  # noqa
            )
            click.secho("Deleting database...", fg="green")
            self.docker_helper.execute_cli_command(
                project_shortname, 'invenio db destroy --yes-i-know')
            click.secho("Deleting indices...", fg="green")
            self.docker_helper.execute_cli_command(
                project_shortname,
                'invenio index destroy --force --yes-i-know')
            click.secho("Purging queues...", fg="green")
            self.docker_helper.execute_cli_command(
                project_shortname, 'invenio index queue init purge')

        if not self.cli_config.get_services_setup():
            click.secho("Creating database...", fg="green")
            self.docker_helper.execute_cli_command(
                project_shortname, 'invenio db init create')

            click.secho("Creating files location...", fg="green")
            self.docker_helper.execute_cli_command(
                project_shortname,
                "invenio files location create --default default-location "
                "${INVENIO_INSTANCE_PATH}/data"
            )

            click.secho("Creating admin role...", fg="green")
            self.docker_helper.execute_cli_command(
                project_shortname, 'invenio roles create admin')

            click.secho(
                "Assigning superuser access to admin role...", fg="green")
            self.docker_helper.execute_cli_command(
                project_shortname,
                'invenio access allow superuser-access role admin')

            click.secho("Creating indices...", fg="green")
            self.docker_helper.execute_cli_command(
                project_shortname, 'invenio index init')

            self.cli_config.update_services_setup(True)

        # statics and assets are always regenerated
        self.update_statics_and_assets(install=install)

        click.secho(
            'Instance running!\nVisit https://127.0.0.1', fg='green')

    def demo(self):
        """Add demo records into the instance."""
        project_shortname = self.cli_config.get_project_shortname()

        # TODO: Shall we call ensure containers? If so move to
        # parent object. Noentheless, the way of starting in
        # container mode ensures the containers are up
        self.docker_helper.execute_cli_command(
            project_shortname, 'invenio rdm-records demo')

    def stop(self):
        """Stops containers."""
        click.secho("Stopping containers...", fg="green")
        self.docker_helper.stop_containers()
        click.secho('Stopped containers', fg='green')

    def destroy(self):
        """Destroys the instance's virtualenv and containers."""
        try:
            subprocess.run(['pipenv', '--rm'], check=True)
            click.secho('Virtual environment destroyed', fg='green')
        except subprocess.CalledProcessError:
            click.secho('The virtual environment was '
                        'not removed as it was not '
                        'created by pipenv', fg='red')

        self.docker_helper.destroy_containers()
        self.cli_config.update_services_setup(False)
        click.secho('Destroyed containers', fg='green')
