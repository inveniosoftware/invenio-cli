# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Local and Containerized Commands."""

import os
import subprocess
import time
from distutils import dir_util

import click

from . import filesystem
from .docker_helper import DockerHelper


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
            self.environment = ContainerizedCommands()

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
        subprocess.run(command)

    def _update_instance_path(self):
        """Update path to instance in config."""
        path = subprocess.run(
            ['pipenv', 'run', 'invenio', 'shell', '--no-term-title',
                '-c', '"print(app.instance_path, end=\'\')"'],
            check=True, universal_newlines=True, stdout=subprocess.PIPE
        ).stdout.strip()
        self.cli_config.update_instance_path(path)

    def _symlink_project_config(self):
        project_config = 'invenio.cfg'
        click.secho("Symlinking {}...".format(project_config), fg="green")
        target_path = self.cli_config.get_project_dir() / project_config
        link_path = self.cli_config.get_instance_path() / project_config
        filesystem.force_symlink(target_path, link_path)

    def _symlink_templates(self):
        """Symlink the templates folder."""
        templates = 'templates'
        click.secho('Symlinking {}/...'.format(templates), fg='green')
        target_path = self.cli_config.get_project_dir() / templates
        link_path = self.cli_config.get_instance_path() / templates
        filesystem.force_symlink(target_path, link_path)

    def _symlink_assets_templates(self, files_to_link):
        """Symlink the assets folder."""
        assets = 'assets'
        click.secho('Symlinking {}/...'.format(assets), fg='green')

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

    def update_statics_and_assets(self, install):
        """High-level command to update scss/js/images... files."""
        click.secho('Collecting statics and assets...', fg='green')
        # Collect into statics/ folder
        command = ['pipenv', 'run', 'invenio', 'collect', '--verbose']
        subprocess.run(command)
        # Collect into assets/ folder
        command = ['pipenv', 'run', 'invenio', 'webpack', 'create']
        subprocess.run(command)

        if install:
            click.secho('Installing js dependencies...', fg='green')
            # Installs in assets/node_modules/
            command = ['pipenv', 'run', 'invenio', 'webpack', 'install']
            subprocess.run(command)

        copied_files = self._copy_statics_and_assets()
        self._symlink_assets_templates(copied_files)

        click.secho('Building assets...', fg='green')
        command = ['pipenv', 'run', 'invenio', 'webpack', 'build']
        subprocess.run(command)

    def build(self, pre, lock):
        """Local build."""
        self._install_py_dependencies(pre, lock)
        self._update_instance_path()
        self._symlink_project_config()
        self._symlink_templates()
        self.update_statics_and_assets(install=True)

    def services(self, force):
        """Local start of containers (services).

        NOTE: We use check=True to mimic set -e from original setup script
              i.e. if a command fails, an exception is raised
        """
        click.secho('Starting local services (containers)...', fg='green')
        docker_helper = DockerHelper(local=True)
        docker_helper.start_containers()
        time.sleep(30)  # Give time to the containers to start properly

        if force:
            command = [
                'pipenv', 'run', 'invenio', 'shell', '--no-term-title', '-c',
                "import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')"  # noqa
            ]
            subprocess.run(command, check=True)

            command = [
                'pipenv', 'run', 'invenio', 'db', 'destroy', '--yes-i-know',
            ]
            subprocess.run(command, check=True)

            command = [
                'pipenv', 'run', 'invenio', 'index', 'destroy',
                '--force', '--yes-i-know',
            ]
            subprocess.run(command, check=True)

            command = [
                'pipenv', 'run', 'invenio', 'index', 'queue', 'init', 'purge']
            subprocess.run(command, check=True)

        # If re-run, this doesn't throw an error
        command = ['pipenv', 'run', 'invenio', 'db', 'init', 'create']
        subprocess.run(command, check=True)

        # If re-run, this throws an error
        # TODO: invenio-files-rest should make it idempotent
        command = [
            'pipenv', 'run', 'invenio', 'files', 'location', '--default',
            'default-location',
            "{}/data".format(self.cli_config.get_instance_path())
        ]
        subprocess.run(command, check=True)

        # If re-run, this throws an error
        # TODO: invenio-accounts should have a cli for find_or_create_role
        command = ['pipenv', 'run', 'invenio', 'roles', 'create', 'admin']
        subprocess.run(command, check=True)

        # If re-run, this doesn't throw an error
        command = [
            'pipenv', 'run', 'invenio', 'access', 'allow',
            'superuser-access', 'role', 'admin'
        ]
        subprocess.run(command, check=True)

        # If re-run, this throws an error
        command = ['pipenv', 'run', 'invenio', 'index', 'init']
        subprocess.run(command, check=True)

    def demo(self):
        """Add demo records into the instance."""
        click.secho("Making sure containers are started...", fg="green")
        docker_helper = DockerHelper(local=True)
        docker_helper.start_containers()
        time.sleep(30)  # Give time for the containers to start properly

        command = ['pipenv', 'run', 'invenio', 'rdm-records', 'demo']
        subprocess.run(command, check=True)


class ContainerizedCommands(object):
    """Containerized environment CLI commands."""

    def __init__(self):
        """Constructor."""
        pass
