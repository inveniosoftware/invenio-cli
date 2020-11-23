# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from os import listdir

import click

from ..helpers.docker_helper import DockerHelper
from ..helpers.process import run_cmd, ProcessResponse
from ..helpers.services import wait_for_services
from .commands import Commands


class ContainersCommands(Commands):
    """Containerized environment CLI commands."""

    def __init__(self, cli_config, docker_helper=None):
        """Constructor."""
        docker_helper = docker_helper or \
            DockerHelper(cli_config.get_project_shortname(), local=False)

        super(ContainersCommands, self).__init__(cli_config, docker_helper)

    def build(self, pull=True, cache=True):
        """Build images.

        :param pull: Attempt to pull newer versions of the images.
        :param cache: Use cached images and layers.
        """
        locked = 'Pipfile.lock' in listdir('.')
        if not locked:
            return ProcessResponse(
                error="Dependencies were not locked. " +
                      "Please run `invenio-cli packages lock`.",
                status_code=1,
            )

        self.docker_helper.build_images(pull, cache)

    def _cleanup(self, project_shortname="/opt/var/instance/"):
        """Execute cleanup commands."""
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
        self.cli_config.update_services_setup(False)

    def _setup(self, project_shortname="/opt/var/instance/"):
        """Initialize services."""
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

    def demo(self, project_shortname):
        """Add demo records into the instance."""
        self.docker_helper.execute_cli_command(
            project_shortname, 'invenio rdm-records demo')

    def setup(self, force, demo_data=True, stop=False):
        """Setup containerize services.

        :param force: Remove existing content (db, indices, etc.).
        :param demo_data: Include demo records.
        :param stop: Stop services after setup.
        """
        self.ensure_containers_running()
        project_shortname = self.cli_config.get_project_shortname()
        if force:
            self._cleanup(project_shortname)
        if not self.cli_config.get_services_setup():
            self._setup(project_shortname)
        if demo_data:
            self.demo(project_shortname)
        if stop:
            self.docker_helper.stop_containers()

        # FIXME: Implemente proper error control.
        # Use run_cmd and check output instead of run_interactive
        return ProcessResponse(
            output="Successfully setup all services.",
            status_code=0
        )

    def start(self, lock=False, build=False, setup=False, demo_data=True,
              services=True):
        """Start service and application containers.

        :param lock: Lock dependencies.
        :param build: Build containers if not built.
        :param setup: Setup services (db, indices, etc.).
        :param demo_data: Include demo records.
        :param services: Start services or only the application containers.
                         This option is incompatible will all the other flags.
        """
        if lock:
            # FIXME: Should this params be accepted? sensible defaults?
            self.lock(pre=True, dev=True)
        if build:
            self.build()

        if services and setup:
            # NOTE: Setup will boot up all service and not bring down
            self.setup(force=True, demo_data=demo_data)
            # FIXME: Should control errors and return proper output
            return

        # NOTE: Needed in case there is no setup
        self.docker_helper.start_containers(app_only=not services)
        # FIXME: Should control errors and return proper output
        return


