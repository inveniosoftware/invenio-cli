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

    @classmethod
    def extract_template_name(cls, template):
        """Extract template name from a template URL."""
        name = template.rstrip('/').rpartition("/")[2]
        git = '.git'
        if name.endswith(git):
            name = name[:-len(git)]
        return name

    def __init__(self, flavour, template_checkout):
        """Constructor.

        :param flavour: "RDM" or something else: String
        :param cookiecutter: tuple of (template: URL, checkout: String)
        """
        self.tmp_file = None
        self.template_name = None
        self.flavour = flavour

        if self.flavour.upper() == 'RDM':
            self.template = (
                template_checkout[0] or
                'https://github.com/inveniosoftware/'
                'cookiecutter-invenio-rdm.git'
            )
            self.template_name = self.extract_template_name(self.template)
            self.checkout = template_checkout[1] or 'v0.9.0'

    def cookiecutter(self):
        """Wrap cookiecutter call."""
        return cookiecutter(
            config_file=self.create_and_dump_config_file(),
            **self.repository()
        )

    def repository(self):
        """Get the cookiecutter repository options."""
        return {
            'template': self.template,
            # NOTE: if template is not a git url, then checkout is ignored
            'checkout': self.checkout
        }

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
