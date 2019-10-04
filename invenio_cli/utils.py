# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


import subprocess


class DockerCompose(object):

    def create_containers(dev, cwd):
        command = ['docker-compose',
                   '-f', 'docker-compose.yml', 'up', '--no-start']
        if dev:
            command[2] = 'docker-compose.dev.yml'

        subprocess.call(command, cwd=cwd)

    def start_containers(dev, cwd, bg):
        command = ['docker-compose',
                   '-f', 'docker-compose.yml', 'up', '--no-recreate']

        if dev:
            command[2] = 'docker-compose.dev.yml'
        if bg:
            command.append('-d')

        subprocess.call(command, cwd=cwd)

    def stop_containers(cwd):
        subprocess.call(['docker-compose', 'stop'], cwd=cwd)

    def destroy_containers(dev, cwd):
        command = ['docker-compose', '-f', 'docker-compose.yml', 'down']
        if dev:
            command[2] = 'docker-compose.dev.yml'

        subprocess.call(command, cwd=cwd)


def cookiecutter_repo(flavor):

    if flavor.upper() == 'RDM':
        return {
                'template': 'https://github.com/inveniosoftware/cookiecutter-invenio-rdm.git',
                'checkout': 'dev'
            }