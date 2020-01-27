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


class InvenioCLIConfig(object):
    """Invenio-cli configuration."""

    CONFIG_FILENAME = '.invenio'
    CLI_SECTION = 'cli'
    CLI_PROJECT_NAME = 'project_shortname'
    CLI_FLAVOUR = 'flavour'
    CLI_LOGFILE = 'logfile'
    COOKIECUTTER_SECTION = 'cookiecutter'
    FILES_SECTION = 'files'

    def __init__(self, flavour=None, verbose=False):
        """Initialize builder.

        :param flavour: Flavour name.
        """
        self.flavour = None
        self.project_shortname = None
        self.log_config = None
        self.config = ConfigParser()
        self.config.read(CONFIG_FILENAME)

        # There is a .invenio config file
        if os.path.isfile(CONFIG_FILENAME):
            try:
                self.flavour = self.config[CLI_SECTION][CLI_FLAVOUR]
                self.project_shortname = \
                    self.config[CLI_SECTION][CLI_PROJECT_NAME]
                self.log_config = LoggingConfig(
                    logfile=self.config[CLI_SECTION][CLI_LOGFILE],
                    verbose=verbose
                )
            except KeyError:
                logging.error(
                    '{0}, {1} or {2} not configured in CLI section'.format(
                        CLI_PROJECT_NAME, CLI_LOGFILE, CLI_FLAVOUR
                    ))
                exit(1)
        elif flavour:
            # There is no .invenio file but the flavour was provided via CLI
            self.flavour = flavour
        else:
            # No value for flavour in .invenio nor CLI
            logging.error('No flavour specified.')
            exit(1)

    def read(self, fullpath):
        """Read invenio-cli config file."""
        pass

    @classmethod
    def write(cls, project_dir, flavour, replay):
        """Write invenio-cli config file.

        :param project_dir: Folder to write the config file into
        :param replay: dict of cookiecutter replay
        """
        config_parser = ConfigParser()

        # CLI parameters section
        config_parser[cls.CLI_SECTION] = {}
        config_parser[cls.CLI_SECTION]['flavour'] = flavour
        # config_parser[cls.CLI_SECTION]['project_shortname'] = \
        #     os.path.basename(project_dir)
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
