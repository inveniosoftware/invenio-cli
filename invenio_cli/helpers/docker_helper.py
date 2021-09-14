# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI Docker Compose class."""

import re

import docker

from .process import ProcessResponse, run_cmd, run_interactive

DOCKER_COMPOSE_VERSION_DASH = '1.21.0'


class DockerHelper(object):
    """Utility class to interact with docker-compose."""

    def __init__(self, project_shortname, local=True, log_config=None):
        """Constructor."""
        super(DockerHelper, self).__init__()
        self.container_prefix = self._normalize_name(project_shortname)
        self.local = local
        self.docker_client = docker.from_env()

    def _normalize_name(self, project_shortname):
        """Normalize the container name according to the compose version.

        Docker-Compose introduced support for dash and underscore in
        version 1.21.0.
        """
        dc_version_string = run_cmd(['docker-compose', '--version'])
        groups = re.search(r'[0-9].[0-9]*.[0-9]*', dc_version_string.output)
        dc_version = groups.group(0)

        if dc_version < DOCKER_COMPOSE_VERSION_DASH:
            return re.sub(r'[^a-z0-9]', '', project_shortname)
        else:
            return project_shortname

    def build_images(self, pull=False, cache=True):
        """Build images.

        :param pull: Adds --pull to the docker-compose command.
        :param cache: Removes --no-cache to the docker-compose command.
        """
        command = [
            'docker-compose',
            '--file',
            'docker-compose.full.yml',
            'build',
        ]
        if pull:
            command.append('--pull')
        if not cache:
            command.append('--no-cache')

        # FIXME: To get real-time output
        return run_interactive(command)

    def start_containers(self, app_only=False):
        """Start containers according to the specified environment.

        :param app_only: Boot up only ui and api containers.
        """
        command = [
            'docker-compose',
            '--file',
            'docker-compose.yml' if self.local else 'docker-compose.full.yml',
            'up',
            '-d'  # --detach not supported in 1.17.0
        ]

        if app_only:
            command.extend(['web-ui', 'web-api'])

        return run_cmd(command)

    def stop_containers(self):
        """Stop currently running containers."""
        command = ['docker-compose', '--file', 'docker-compose.full.yml',
                   'stop']
        return run_cmd(command)

    def destroy_containers(self):
        """Stop and remove all containers, volumes and images."""
        command = ['docker-compose', '--file', 'docker-compose.full.yml',
                   'down', '--volumes']

        return run_cmd(command)

    def execute_cli_command(self, project_shortname, command):
        """Execute an invenio CLI command in the API container."""
        container_name = '{}_web-ui_1'.format(self.container_prefix)
        container = self.docker_client.containers.get(container_name)
        status = container.exec_run(
            cmd='/bin/bash -c "{}"'.format(command.replace('"', '\\"')),
            tty=True,
            stdout=True,
            stderr=True)
        # FIXME: What happens when exec_run fails? handle exception.
        return ProcessResponse(
            output=status.output.decode("utf-8").strip(),
            status_code=status.exit_code
        )
