# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from os import listdir
from subprocess import run as run_proc

import click

from ..helpers.docker_helper import DockerHelper
from ..helpers.services import wait_for_services
from .commands import Commands


class ContainersCommands(Commands):
    """Containerized environment CLI commands."""

    def __init__(self, cli_config, docker_helper=None):
        """Constructor."""
        docker_helper = docker_helper or \
            DockerHelper(cli_config.get_project_shortname(), local=False)

        super(ContainersCommands, self).__init__(cli_config, docker_helper)

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
        src_dir = src_dir / '.'
        dst_dir = '/opt/invenio/var/instance/static/'
        self.docker_helper.copy2(src_dir, dst_dir)

        src_dir = self.cli_config.get_project_dir() / 'assets'
        # src_dir MUST be '<dir>/.' for docker cp to work
        src_dir = src_dir / '.'
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

        locked = 'Pipfile.lock' in listdir('.')
        if not locked:
            run_proc(command, check=True)

    def containerize(self, pre, force, install):
        """Launch fully containerized application."""
        self._lock_python_dependencies(pre)

        click.secho('Making sure containers are up...', fg='green')
        self.docker_helper.start_containers()

        project_shortname = self.cli_config.get_project_shortname()

        wait_for_services(
            services=["redis", self.cli_config.get_db_type(), "es"],
            project_shortname=project_shortname,
        )

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
