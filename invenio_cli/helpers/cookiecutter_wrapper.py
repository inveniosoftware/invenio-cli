# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019-2021 CERN.
# Copyright (C) 2019-2021 Northwestern University.
# Copyright (C) 2022 Forschungszentrum Jülich GmbH.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Cookiecutter Config class."""

import tempfile
from configparser import ConfigParser

import yaml
from cookiecutter import replay
from cookiecutter.config import DEFAULT_CONFIG
from cookiecutter.main import cookiecutter

from .cli_config import CLIConfig


class CookiecutterWrapper(object):
    """Cookiecutter helper object for InvenioCLI."""

    @classmethod
    def extract_template_name(cls, template):
        """Extract template name from a template URL."""
        name = template.rstrip("/").rpartition("/")[2]
        git = ".git"
        if name.endswith(git):
            name = name[: -len(git)]
        return name

    def __init__(self, flavour, **kwargs):
        """Constructor.

        :param flavour: "RDM", "ILS" or something else: String

        :Keyword Arguments:
          * template: URL
          * checkout: String,
          * user_input: Boolean
          * config: String
        """
        self.tmp_file = None

        self.flavour = flavour
        self.template_name = kwargs.get("template", None)
        self.checkout = kwargs.get("checkout", None)

        self.config = kwargs.get("config", None)
        self.no_input = kwargs.get("no_input", False)
        self.replay = {}
        if self.config:
            self.no_input = True
            config = ConfigParser()
            config.read(self.config)
            # load values to be passed to cookiecutter from an .invenio file
            self.replay = dict(config[CLIConfig.COOKIECUTTER_SECTION].items())

        if self.flavour.upper() == "RDM":
            self.template = (
                self.template_name
                or "https://github.com/inveniosoftware/cookiecutter-invenio-rdm.git"
            )
            self.template_name = self.extract_template_name(self.template)
            self.checkout = self.checkout or "v11.0"

        if self.flavour.upper() == "ILS":
            self.template = (
                self.template_name
                or "https://github.com/inveniosoftware/cookiecutter-invenio-ils.git"
            )
            self.template_name = self.extract_template_name(self.template)
            self.checkout = self.checkout or "v1.0.0rc.1"

    def cookiecutter(self):
        """Wrap cookiecutter call."""
        # build actual kwargs
        cookiecutter_kwargs = {
            "template": self.template,
            # NOTE: if template is not a git url, then checkout is ignored
            "checkout": self.checkout,
        }
        if self.config or self.no_input:
            cookiecutter_kwargs["no_input"] = self.no_input
            cookiecutter_kwargs["extra_context"] = self.replay

        # run cookiecutter
        return cookiecutter(
            config_file=self.create_and_dump_config_file(), **cookiecutter_kwargs
        )

    def create_and_dump_config_file(self):
        """Create a tmp file to store used configuration."""
        if not self.tmp_file:
            self.tmp_file = tempfile.NamedTemporaryFile(mode="w+")

        config = DEFAULT_CONFIG.copy()
        # BUG: when dumping {}, it's read back as a string '{}'
        config["default_context"] = None
        config["replay_dir"] = tempfile.gettempdir()

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
