# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2024 CERN.
# Copyright (C) 2019-2020 Northwestern University.
# Copyright (C) 2021 Esteban J. G. Gabancho.
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio-cli configuration file."""

from configparser import ConfigParser
from pathlib import Path

from ..errors import InvenioCLIConfigError
from .filesystem import get_created_files
from .process import ProcessResponse


class CLIConfig(object):
    """Invenio-cli configuration.

    It provides a combined interface to the local CLI configuration which
    is typically split between a
        .invenio file with general project configuration
        .invenio.private with per machine configuration
                         (not version controlled)
    """

    CONFIG_FILENAME = ".invenio"
    PRIVATE_CONFIG_FILENAME = ".invenio.private"
    CLI_SECTION = "cli"
    COOKIECUTTER_SECTION = "cookiecutter"
    FILES_SECTION = "files"

    def __init__(self, project_dir="./"):
        """Constructor.

        :param config_dir: Path to general cli config file.
        """
        self.config_path = Path(project_dir) / self.CONFIG_FILENAME
        self.config = ConfigParser()
        self.private_config_path = Path(project_dir) / self.PRIVATE_CONFIG_FILENAME
        self.private_config = ConfigParser()

        try:
            with open(self.config_path) as cfg_file:
                self.config.read_file(cfg_file)
        except FileNotFoundError as e:
            raise InvenioCLIConfigError(
                "Missing '{0}' file in current directory. "
                "Are you in the project folder?".format(e.filename),
            )

        try:
            with open(self.private_config_path) as cfg_file:
                self.private_config.read_file(cfg_file)
        except FileNotFoundError:
            CLIConfig._write_private_config(Path(project_dir))
            with open(self.private_config_path) as cfg_file:
                self.private_config.read_file(cfg_file)

    @property
    def python_packages_manager(self):
        """Get python packages manager."""
        return self.config[CLIConfig.CLI_SECTION].get("python_packages_manager", "pip")

    @property
    def javascript_packages_manager(self):
        """Get javascript packages manager."""
        return self.config[CLIConfig.CLI_SECTION].get(
            "javascript_packages_manager", "npm"
        )

    @property
    def assets_builder(self):
        """Get assets builder."""
        return self.config[CLIConfig.CLI_SECTION].get("assets_builder", "webpack")

    def get_project_dir(self):
        """Returns path to project directory."""
        return self.config_path.parent.resolve()

    def get_instance_path(self, throw=True):
        """Returns path to application instance directory.

        If not set yet, raises an InvenioCLIConfigError.
        """
        path = self.private_config[CLIConfig.CLI_SECTION].get("instance_path")
        if path:
            return Path(path)
        elif throw:
            raise InvenioCLIConfigError("Accessing unset 'instance_path'")

    def update_instance_path(self, new_instance_path):
        """Updates path to application instance directory."""
        self.private_config[CLIConfig.CLI_SECTION]["instance_path"] = str(
            new_instance_path
        )

        with open(self.private_config_path, "w") as configfile:
            self.private_config.write(configfile)

        return ProcessResponse(
            output=f"Instance path updated (new value {new_instance_path}).",
            status_code=0,
        )

    def get_services_setup(self):
        """Returns bool whether services have been setup or not."""
        return self.private_config.getboolean(CLIConfig.CLI_SECTION, "services_setup")

    def update_services_setup(self, is_setup):
        """Updates path to application instance directory."""
        self.private_config[CLIConfig.CLI_SECTION]["services_setup"] = str(is_setup)

        with open(self.private_config_path, "w") as configfile:
            self.private_config.write(configfile)

        return ProcessResponse(
            output=f"Service setup status updated (new value {is_setup}).",
            status_code=0,
        )

    def get_project_shortname(self):
        """Returns the project's shortname."""
        return self.config[CLIConfig.COOKIECUTTER_SECTION]["project_shortname"]

    def get_search_port(self):
        """Returns the search port."""
        return self.config[CLIConfig.COOKIECUTTER_SECTION].get("search_port", "9200")

    def get_search_host(self):
        """Returns the search host."""
        return self.config[CLIConfig.COOKIECUTTER_SECTION].get(
            "search_host",
            "localhost",
        )

    def get_web_port(self):
        """Returns web port."""
        return self.config[CLIConfig.COOKIECUTTER_SECTION].get("web_port", "5000")

    def get_web_host(self):
        """Returns web host."""
        return self.config[CLIConfig.COOKIECUTTER_SECTION].get("web_host", "127.0.0.1")

    def get_db_type(self):
        """Returns the database type (mysql, postgresql)."""
        return self.config[CLIConfig.COOKIECUTTER_SECTION]["database"]

    def get_search_type(self):
        """Returns the search type (opensearch1, elasticsearch7)."""
        sections = self.config[CLIConfig.COOKIECUTTER_SECTION]
        if "elasticsearch" in sections:
            # cookiecutter < v10
            version = sections["elasticsearch"]
            return f"elasticsearch{version}"
        elif "search" in sections:
            # cookiecutter >= v10
            return sections["search"]
        else:
            raise InvenioCLIConfigError(
                "`search` or `elasticsearch` field not set in .invenio file"
            )

    def get_file_storage(self):
        """Returns the file storage (local, s3, etc.)."""
        return self.config[CLIConfig.COOKIECUTTER_SECTION]["file_storage"]

    def get_author_email(self):
        """Returns the email of the author/owner of the project."""
        return self.config[CLIConfig.COOKIECUTTER_SECTION]["author_email"]

    def get_author_name(self):
        """Returns the name of the author/owner of the project."""
        return self.config[CLIConfig.COOKIECUTTER_SECTION]["author_name"]

    @classmethod
    def _write_private_config(cls, project_dir):
        """Write per-instance config file."""
        config_parser = ConfigParser()
        config_parser[cls.CLI_SECTION] = {}
        config_parser[cls.CLI_SECTION]["services_setup"] = str(False)
        private_config_path = project_dir / cls.PRIVATE_CONFIG_FILENAME
        with open(private_config_path, "w") as configfile:
            config_parser.write(configfile)

    @classmethod
    def write(cls, project_dir, flavour, replay):
        """Write invenio-cli config files.

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
        config_parser[cls.CLI_SECTION]["flavour"] = flavour
        config_parser[cls.CLI_SECTION]["logfile"] = "/logs/invenio-cli.log"

        # Cookiecutter user input section
        config_parser[cls.COOKIECUTTER_SECTION] = {}
        for key, value in replay[cls.COOKIECUTTER_SECTION].items():
            config_parser[cls.COOKIECUTTER_SECTION][key] = value

        # Generated files section
        config_parser[cls.FILES_SECTION] = get_created_files(project_dir)

        config_path = project_dir / cls.CONFIG_FILENAME
        with open(config_path, "w") as configfile:
            config_parser.write(configfile)

        # Custom to machine (not version controlled)
        cls._write_private_config(project_dir)

        return project_dir
