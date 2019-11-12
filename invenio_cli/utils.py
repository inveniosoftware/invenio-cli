# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI Utility classes and functions."""

import hashlib
import json
import subprocess
import tempfile
from os import listdir
from os.path import isdir
from pathlib import Path

import yaml
from cookiecutter.config import DEFAULT_CONFIG


class DockerCompose(object):
    """Utility class to interact with docker-compose."""

    def create_images(dev):
        """Create images according to the specified environment."""
        command = ['docker-compose',
                   '-f', 'docker-compose.full.yml', 'up', '--no-start']
        if dev:
            command[2] = 'docker-compose.yml'

        subprocess.call(command)

    def start_containers(dev, bg):
        """Start containers according to the specified environment."""
        command = ['docker-compose',
                   '-f', 'docker-compose.full.yml', 'up', '--no-recreate']

        if dev:
            command[2] = 'docker-compose.yml'

        if bg:
            command.append('-d')
            subprocess.call(command, )
        else:
            subprocess.Popen(command,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def stop_containers():
        """Stop currently running containers."""
        subprocess.call(['docker-compose', 'stop'])

    def destroy_containers(dev):
        """Stop and remove all containers, volumes and images."""
        command = ['docker-compose', '-f', 'docker-compose.full.yml',
                   'down', '--volumes']
        if dev:
            command[2] = 'docker-compose.yml'

        subprocess.call(command)


class Cookiecutter(object):
    """Cookiecutter helper object for InvenioCLI."""

    def __init__(self):
        """Cookiecutter helper constructor."""
        self.tmp_file = None
        self.template = None

    def repository(self, flavor):
        """Get the cookiecutter repository of a flavour."""
        if flavor.upper() == 'RDM':
            repo = {
                    'template': 'https://github.com/inveniosoftware/' +
                                'cookiecutter-invenio-rdm.git',
                    'checkout': 'v1.0.0a2'
                }
            self.template = 'cookiecutter-invenio-rdm.json'
            return repo

    def create_and_dump_config(self):
        """Create a tmp file to store cookicutters used configuration."""
        if not self.tmp_file:
            self.tmp_file = \
                tempfile.NamedTemporaryFile(mode='w+', delete=False)

        config = DEFAULT_CONFIG.copy()
        # Bug when dumping default {} it's read a string
        config['default_context'] = None
        config['replay_dir'] = tempfile.gettempdir()

        yaml.dump(config, self.tmp_file)

        return self.tmp_file.name

    def get_replay(self):
        """Retrieve cookiecutters user input values."""
        replay_path = Path(tempfile.gettempdir()) / self.template

        with open(replay_path) as replay_file:
            return json.load(replay_file)

        return {}

    def remove_config(self):
        """Remove the tmp file."""
        if self.tmp_file:
            self.tmp_file.close()


# DEfining buffer size to avoid using too much memory
BUF_SIZE = 65536  # 64 KB


def hash_file(path_to_file):
    """Hash file to check for consistency."""
    sha256 = hashlib.sha256()

    with open(path_to_file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)

    return sha256.hexdigest()


def get_created_files(folder):
    """Return the generated tree of files (and their hash) and folders."""
    files = {}
    for name in listdir(folder):
        path = Path(folder)  # Current path

        # Add files and their hash
        if not isdir(path / name):
            files[name] = hash_file(path / name)
        # Add dirs and their files
        else:
            files[name] = get_created_files(path / name)

    return files
