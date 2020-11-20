# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from subprocess import CalledProcessError
from subprocess import run as run_proc

import click

from ..helpers.docker_helper import DockerHelper
from ..helpers.env import env
from ..helpers.services import HEALTHCHECKS


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

    def shell(self):
        """Start a shell in the virtual environment."""
        command = ['pipenv', 'shell', ]
        run_proc(command, check=True)

    def pyshell(self, debug=False):
        """Start a Python shell."""
        with env(FLASK_ENV='development' if debug else 'production'):
            command = ['pipenv', 'run', 'invenio', 'shell']
            run_proc(command, check=True)

    def status(self, services, verbose):
        """Checks the status of the given service."""
        project_shortname = self.cli_config.get_project_shortname()

        for service in services:
            check = HEALTHCHECKS.get(service)
            if check:
                if check(
                    filepath="docker-services.yml",
                    verbose=verbose,
                    project_shortname=project_shortname,
                ):
                    click.secho(f"{service} up and running.", fg="green")
                else:
                    click.secho(
                        f"{service}: unable to connect or bad status" +
                        " response.",
                        fg="red"
                    )
            else:
                click.secho(
                    f"{service}: no healthcheck function defined.",
                    fg="yellow"
                )

    def stop(self):
        """Stops containers."""
        click.secho("Stopping containers...", fg="green")
        self.docker_helper.stop_containers()
        click.secho('Stopped containers', fg='green')

    def destroy(self):
        """Destroys the instance's virtualenv and containers."""
        try:
            run_proc(['pipenv', '--rm'], check=True)
            click.secho('Virtual environment destroyed', fg='green')
        except CalledProcessError:
            click.secho('The virtual environment was '
                        'not removed as it was not '
                        'created by pipenv', fg='red')

        self.docker_helper.destroy_containers()
        self.cli_config.update_services_setup(False)
        click.secho('Destroyed containers', fg='green')
