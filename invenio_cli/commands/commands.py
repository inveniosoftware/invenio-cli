# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from subprocess import CalledProcessError

import click

from ..helpers.docker_helper import DockerHelper
from ..helpers.env import env
from ..helpers.process import run_cmd, run_interactive
from ..helpers.services import HEALTHCHECKS, wait_for_services


class Commands(object):
    """Abstraction over CLI commands that are either local or containerized."""

    def __init__(self, cli_config, docker_helper=None):
        """Constructor.

        :param cli_config: :class:CLIConfig instance
        :param docker_helper: :class:DockerHelper instance, defaults to
            containerized docker file (`docker-compose.full.yml`).
        """
        self.cli_config = cli_config
        self.docker_helper = docker_helper or \
            DockerHelper(cli_config.get_project_shortname(), local=False)

    def ensure_containers_running(self):
        """Ensures containers are running.

        NOTE: Used by ContainersCommands, InstallCommands and ServicesCommands
        """
        click.secho('Making sure containers are up...', fg='green')
        project_shortname = self.cli_config.get_project_shortname()
        self.docker_helper.start_containers()

        wait_for_services(
            services=["redis", self.cli_config.get_db_type(), "es"],
            project_shortname=project_shortname,
        )

    def shell(self):
        """Start a shell in the virtual environment."""
        command = ['pipenv', 'shell', ]
        return run_cmd(command)

    def pyshell(self, debug=False):
        """Start a Python shell."""
        with env(FLASK_ENV='development' if debug else 'production'):
            command = ['pipenv', 'run', 'invenio', 'shell']
            return run_interactive(command)

    def status(self, services, verbose):
        """Checks the status of the given service.

        :returns: A list of the same length than services. Each item will be a
                  code corresponding to: 0 success, 1 failure, 2 healthcheck
                  not defined.
        """
        project_shortname = self.cli_config.get_project_shortname()
        statuses = []
        for service in services:
            check = HEALTHCHECKS.get(service)
            if check:
                result = check(
                    filepath="docker-services.yml",
                    verbose=verbose,
                    project_shortname=project_shortname,
                )
                # Append 0 if OK, else 1
                # FIXME: Deal with codes higher than 1. Needed?
                code = 0 if result.status_code == 0 else 1
                statuses.append(code)
            else:
                statuses.append(2)

        return statuses

    def stop(self):
        """Stops containers."""
        return self.docker_helper.stop_containers()

    def destroy(self):
        """Destroys the instance's virtualenv and containers."""
        try:
            run_cmd(['pipenv', '--rm'])
        except CalledProcessError:
            # TODO: Control possible errors from pipenv run
            # `pipenv` not installed, not in a pipenv managed venve, etc.
            pass

        response = self.docker_helper.destroy_containers()
        # TODO: Check the response status code before updating services setup.
        # Careful not to leave in an inconsistent state.
        self.cli_config.update_services_setup(False)

        return response

    def lock(self, pre, dev):
        """Lock Python dependencies."""
        command = ['pipenv', 'install']
        if pre:
            command += ['--pre']
        if dev:
            command += ['--dev']
        # NOTE: Interactive to allow real-time output of pipenv
        return run_interactive(command)
