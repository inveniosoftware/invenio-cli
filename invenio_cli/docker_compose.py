# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI Utility classes and functions."""

import subprocess

from .log import LogPipe


class DockerCompose(object):
    """Utility class to interact with docker-compose."""

    @staticmethod
    def create_images(dev, loglevel):
        """Create images according to the specified environment."""
        # Open logging pipe
        logpipe = LogPipe(loglevel)

        command = ['docker-compose',
                   '-f', 'docker-compose.full.yml', 'up', '--no-start']
        if dev:
            command[2] = 'docker-compose.yml'

        subprocess.call(command, stdout=logpipe, stderr=logpipe)
        # Close logging pipe
        logpipe.close()

    @staticmethod
    def start_containers(dev, bg, loglevel):
        """Start containers according to the specified environment."""
        command = ['docker-compose',
                   '-f', 'docker-compose.full.yml', 'up', '--no-recreate']

        if dev:
            command[2] = 'docker-compose.yml'

        if bg:
            # Open logging pipe
            logpipe = LogPipe(loglevel)

            command.append('-d')
            subprocess.call(command, stdout=logpipe, stderr=logpipe)

            # Close logging pipe
            logpipe.close()
        else:
            # TEST: Is this piping all logs of containers along with server's?
            subprocess.Popen(command,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    @staticmethod
    def stop_containers(loglevel):
        """Stop currently running containers."""
        # Open logging pipe
        logpipe = LogPipe(loglevel)

        subprocess.call(['docker-compose', 'stop'],
                        stdout=logpipe, stderr=logpipe)

        # Close logging pipe
        logpipe.close()

    @staticmethod
    def destroy_containers(dev, loglevel):
        """Stop and remove all containers, volumes and images."""
        # Open logging pipe
        logpipe = LogPipe(loglevel)

        command = ['docker-compose', '-f', 'docker-compose.full.yml',
                   'down', '--volumes']
        if dev:
            command[2] = 'docker-compose.yml'

        subprocess.call(command, stdout=logpipe, stderr=logpipe)

        # Close logging pipe
        logpipe.close()
