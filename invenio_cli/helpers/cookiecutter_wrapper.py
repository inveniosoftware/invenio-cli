# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Cookiecutter Config class."""

import json
import tempfile
from pathlib import Path

import yaml
from cookiecutter import replay
from cookiecutter.config import DEFAULT_CONFIG
from cookiecutter.exceptions import OutputDirExistsException
from cookiecutter.main import cookiecutter


class CookiecutterWrapper(object):
    """Cookiecutter helper object for InvenioCLI."""

    def __init__(self, flavour):
        """Constructor."""
        self.tmp_file = None
        self.template_name = None
        self.flavour = flavour

    def cookiecutter(self):
        """Wrap cookiecutter call."""
        return cookiecutter(
            config_file=self.create_and_dump_config_file(),
            **self.repository()
        )

    def repository(self):
        """Get the cookiecutter repository of a flavour."""
        if self.flavour.upper() == 'RDM':
            self.template_name = 'cookiecutter-invenio-rdm'
            repo = {
                'template': 'https://github.com/inveniosoftware/' +
                            '{}.git'.format(self.template_name),
                # set to cookiecutter release version
                # reset to master in development
                'checkout': 'v1.0.0a5'
            }
            return repo

    def create_and_dump_config_file(self):
        """Create a tmp file to store used configuration."""
        if not self.tmp_file:
            self.tmp_file = tempfile.NamedTemporaryFile(mode='w+')

        config = DEFAULT_CONFIG.copy()
        # BUG: when dumping {}, it's read back as a string '{}'
        config['default_context'] = None
        config['replay_dir'] = tempfile.gettempdir()

        yaml.dump(config, self.tmp_file)

        return self.tmp_file.name

    def remove_config(self):
        """Remove the tmp file."""
        if self.tmp_file:
            self.tmp_file.close()

    def get_replay(self):
        """Retrieve dict of user input values."""
        if self.template_name:
            return replay.load(tempfile.gettempdir(), self.template_name)
