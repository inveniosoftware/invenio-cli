# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI Docker Compose class."""

import logging
import subprocess

import docker

from .log import LogPipe


class DockerCompose(object):
    """Utility class to interact with docker-compose."""

    def __init__(self, dev=True, bg=True, loglevel=logging.WARN,
                 logfile='invenio-cli.log'):
        """Constructor for the DockerCompose helper."""
        super(DockerCompose, self).__init__()
        self.dev = dev
        self.bg = bg
        self.loglevel = loglevel
        self.logfile = logfile
        self.docker_client = docker.from_env()

    def built_image(self, dockerfile, tag):
        """Build docker image."""
        self.docker_client.images.build(dockerfile=dockerfile, tag=tag)

    def create_images(self):
        """Create images according to the specified environment."""
        # Open logging pipe
        logpipe = LogPipe(self.loglevel, self.logfile)

        command = ['docker-compose',
                   '-f', 'docker-compose.full.yml', 'up', '--no-start']
        if self.dev:
            command[2] = 'docker-compose.yml'

        subprocess.call(command, stdout=logpipe, stderr=logpipe)
        # Close logging pipe
        logpipe.close()

    def start_containers(self):
        """Start containers according to the specified environment."""
        command = ['docker-compose',
                   '-f', 'docker-compose.full.yml', 'up', '--no-recreate']

        if self.dev:
            command[2] = 'docker-compose.yml'

        if self.bg:
            # Open logging pipe
            logpipe = LogPipe(self.loglevel, self.logfile)

            command.append('-d')
            subprocess.call(command, stdout=logpipe, stderr=logpipe)

            # Close logging pipe
            logpipe.close()
        else:
            # TEST: Is this piping all logs of containers along with server's?
            subprocess.Popen(command,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def stop_containers(self):
        """Stop currently running containers."""
        # Open logging pipe
        logpipe = LogPipe(self.loglevel, self.logfile)

        subprocess.call(['docker-compose', 'stop'],
                        stdout=logpipe, stderr=logpipe)

        # Close logging pipe
        logpipe.close()

    def destroy_containers(self):
        """Stop and remove all containers, volumes and images."""
        # Open logging pipe
        logpipe = LogPipe(self.loglevel, self.logfile)

        command = ['docker-compose', '-f', 'docker-compose.full.yml',
                   'down', '--volumes']
        if self.dev:
            command[2] = 'docker-compose.yml'

        subprocess.call(command, stdout=logpipe, stderr=logpipe)

        # Close logging pipe
        logpipe.close()
