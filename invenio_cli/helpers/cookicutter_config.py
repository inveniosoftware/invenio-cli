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
from cookiecutter.config import DEFAULT_CONFIG


class CookiecutterConfig(object):
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
                'checkout': 'master'  # set to release version at release time
            }
            self.template = 'cookiecutter-invenio-rdm.json'
            return repo

    def create_and_dump_config(self):
        """Create a tmp file to store cookicutters used configuration."""
        if not self.tmp_file:
            self.tmp_file = \
                tempfile.NamedTemporaryFile(mode='w+')

        config = DEFAULT_CONFIG.copy()
        # BUG: when dumping {}, it's read back as a string '{}'
        config['default_context'] = None
        config['replay_dir'] = tempfile.gettempdir()

        yaml.dump(config, self.tmp_file)

        return self.tmp_file.name

    def get_replay(self):
        """Retrieve cookiecutters user input values."""
        replay_path = Path(tempfile.gettempdir()) / self.template

        with open(replay_path) as replay_file:
            return json.load(replay_file)

    def remove_config(self):
        """Remove the tmp file."""
        if self.tmp_file:
            self.tmp_file.close()
