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

import click

from .filesystem import get_created_files


class CLIConfig(object):
    """Invenio-cli configuration.

    It provides a combined interface to the local CLI configuration which
    is typically split between a
        .invenio file with general project configuration
        .invenio.private with per machine configuration
                         (not version controlled)
    """

    CONFIG_FILENAME = '.invenio'
    PRIVATE_CONFIG_FILENAME = '.invenio.private'
    CLI_SECTION = 'cli'
    COOKIECUTTER_SECTION = 'cookiecutter'
    FILES_SECTION = 'files'

    def __init__(self, project_dir='./', verbose=False):
        """Constructor.

        :param config_dir: Path to general cli config file.
        :param config_path: Absolute path to per machine cli config file.
        """
        self.config_path = Path(project_dir) / self.CONFIG_FILENAME
        self.config = ConfigParser()
        self.private_config_path = (
            Path(project_dir) / self.PRIVATE_CONFIG_FILENAME
        )
        self.private_config = ConfigParser()

        try:
            with open(self.config_path) as cfg_file:
                self.config.read_file(cfg_file)

            with open(self.private_config_path) as cfg_file:
                self.private_config.read_file(cfg_file)

        except FileNotFoundError:
            click.secho(
                "Missing '.invenio' file in current directory. "
                "Are you in the project folder?", fg='red'
            )
            exit(1)

    def get_project_dir(self):
        """Returns path to project directory."""
        return Path(self.private_config[CLIConfig.CLI_SECTION]['project_dir'])

    def get_instance_path(self):
        """Returns path to application instance directory."""
        return Path(
            self.private_config[CLIConfig.CLI_SECTION]['instance_path']
        )

    def update_instance_path(self, new_instance_path):
        """Updates path to application instance directory."""
        self.private_config[CLIConfig.CLI_SECTION]['instance_path'] = \
            str(new_instance_path)

        with open(self.private_config_path, 'w') as configfile:
            self.private_config.write(configfile)

    def get_services_setup(self):
        """Returns bool whether services have been setup or not."""
        return self.private_config.getboolean(
            CLIConfig.CLI_SECTION, 'services_setup'
        )

    def update_services_setup(self, is_setup):
        """Updates path to application instance directory."""
        self.private_config[CLIConfig.CLI_SECTION]['services_setup'] = \
            str(is_setup)

        with open(self.private_config_path, 'w') as configfile:
            self.private_config.write(configfile)

    def get_project_shortname(self):
        """Returns the project's shortname."""
        return self.config[CLIConfig.COOKIECUTTER_SECTION]['project_shortname']

    @classmethod
    def write(cls, project_dir, flavour, replay):
        """Write invenio-cli config file.

        :param project_dir: Folder to write the config file into
        :param flavour: 'RDM' or 'ILS'
        :param replay: dict of cookiecutter replay
        :return: absolute Path to config (project) directory
        """
        config_parser = ConfigParser()
        # Convert to absolute Path because simpler to reason about and pass
        project_dir = Path(project_dir).resolve()

        # Internal to Invenio-cli section
        config_parser[cls.CLI_SECTION] = {}
        config_parser[cls.CLI_SECTION]['flavour'] = flavour
        config_parser[cls.CLI_SECTION]['logfile'] = '/logs/invenio-cli.log'

        # Cookiecutter user input section
        config_parser[cls.COOKIECUTTER_SECTION] = {}
        for key, value in replay[cls.COOKIECUTTER_SECTION].items():
            config_parser[cls.COOKIECUTTER_SECTION][key] = value

        # Generated files section
        config_parser[cls.FILES_SECTION] = get_created_files(project_dir)

        config_path = project_dir / cls.CONFIG_FILENAME
        with open(config_path, 'w') as configfile:
            config_parser.write(configfile)

        # Internal to machine (not version controlled)
        config_parser = ConfigParser()
        config_parser[cls.CLI_SECTION] = {}
        config_parser[cls.CLI_SECTION]['project_dir'] = str(project_dir)
        config_parser[cls.CLI_SECTION]['instance_path'] = ''
        config_parser[cls.CLI_SECTION]['services_setup'] = str(False)
        private_config_path = project_dir / cls.PRIVATE_CONFIG_FILENAME
        with open(private_config_path, 'w') as configfile:
            config_parser.write(configfile)

        return project_dir
