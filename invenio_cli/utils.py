# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University,
#                    Galter Health Sciences Library & Learning Center.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI Utility classes and functions."""

import subprocess


class DockerCompose(object):
    """Utility class to interact with docker-compose."""

    # FIXME: Change name to create_images
    def create_containers(dev, cwd):
        """Create images according to the specified environment."""
        command = ['docker-compose',
                   '-f', 'docker-compose.full.yml', 'up', '--no-start']
        if dev:
            command[2] = 'docker-compose.yml'

        subprocess.call(command, cwd=cwd)

    def start_containers(dev, cwd, bg):
        """Start containers according to the specified environment."""
        command = ['docker-compose',
                   '-f', 'docker-compose.full.yml', 'up', '--no-recreate']

        if dev:
            command[2] = 'docker-compose.yml'

        if bg:
            command.append('-d')
            subprocess.call(command, cwd=cwd)
        else:
            subprocess.Popen(command, cwd=cwd,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def stop_containers(cwd):
        """Stop currently running containers."""
        subprocess.call(['docker-compose', 'stop'], cwd=cwd)

    def destroy_containers(dev, cwd):
        """Stop and remove all containers, volumes and images."""
        command = ['docker-compose', '-f', 'docker-compose.full.yml',
                   'down', '--volumes']
        if dev:
            command[2] = 'docker-compose.yml'

        subprocess.call(command, cwd=cwd)


def cookiecutter_repo(flavor):
    """Utility function. Returns the Cookiecutter repository of a flavour."""
    if flavor.upper() == 'RDM':
        return {
                'template': 'https://github.com/inveniosoftware/' +
                            'cookiecutter-invenio-rdm.git',
                'checkout': 'v1.0.0a1'
            }
