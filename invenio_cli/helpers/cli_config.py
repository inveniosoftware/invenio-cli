# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-cli configuration file."""

import os
from configparser import ConfigParser
from pathlib import Path

from .filesystem import get_created_files


class CLIConfig(object):
    """Invenio-cli configuration."""

    CONFIG_FILENAME = '.invenio'
    CLI_SECTION = 'cli'
    COOKIECUTTER_SECTION = 'cookiecutter'
    FILES_SECTION = 'files'

    def __init__(self, fullpath=CONFIG_FILENAME, verbose=False):
        """Constructor.

        :param flavour: Flavour name.
        """
        self.config = ConfigParser()
        self.fullpath = fullpath
        self.config.read(fullpath)

    def get_project_dir(self):
        """Returns path to project directory."""
        return Path(self.config[CLIConfig.CLI_SECTION]['project_dir'])

    def get_instance_path(self):
        """Returns path to application instance directory."""
        return Path(self.config[CLIConfig.CLI_SECTION]['instance_path'])

    def update_instance_path(self, new_instance_path):
        """Updates path to application instance directory."""
        self.config[CLIConfig.CLI_SECTION]['instance_path'] = \
            str(new_instance_path)

        with open(self.fullpath, 'w') as configfile:
            self.config.write(configfile)

    def get_services_setup(self):
        """Returns bool whether services have been setup or not."""
        return self.config.getboolean(CLIConfig.CLI_SECTION, 'services_setup')

    def update_services_setup(self, is_setup):
        """Updates path to application instance directory."""
        self.config[CLIConfig.CLI_SECTION]['services_setup'] = str(is_setup)

        with open(self.fullpath, 'w') as configfile:
            self.config.write(configfile)

    def get_project_shortname(self):
        """Returns the project's shortname."""
        return self.config[CLIConfig.COOKIECUTTER_SECTION]['project_shortname']

    @classmethod
    def write(cls, project_dir, flavour, replay):
        """Write invenio-cli config file.

        :param project_dir: Folder to write the config file into
        :param flavour: 'RDM' or 'ILS'
        :param replay: dict of cookiecutter replay
        :return: full path to config file
        """
        config_parser = ConfigParser()

        # Internal to Invenio-cli section
        config_parser[cls.CLI_SECTION] = {}
        config_parser[cls.CLI_SECTION]['flavour'] = flavour
        config_parser[cls.CLI_SECTION]['project_dir'] = project_dir
        config_parser[cls.CLI_SECTION]['instance_path'] = ''
        config_parser[cls.CLI_SECTION]['services_setup'] = str(False)
        config_parser[cls.CLI_SECTION]['logfile'] = \
            '{path}/logs/invenio-cli.log'.format(path=project_dir)

        # Cookiecutter user input section
        config_parser[cls.COOKIECUTTER_SECTION] = {}
        for key, value in replay[cls.COOKIECUTTER_SECTION].items():
            config_parser[cls.COOKIECUTTER_SECTION][key] = value

        # Generated files section
        config_parser[cls.FILES_SECTION] = get_created_files(project_dir)

        fullpath = Path(project_dir) / cls.CONFIG_FILENAME
        with open(fullpath, 'w') as configfile:
            config_parser.write(configfile)

        return fullpath
