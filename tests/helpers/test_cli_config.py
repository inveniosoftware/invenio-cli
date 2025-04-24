# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2021 Northwestern University.
# Copyright (C) 2025 KTH Royal Institute of Technology.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module config_file tests."""
import os
import tempfile
from configparser import ConfigParser
from pathlib import Path

import pytest

from invenio_cli.errors import InvenioCLIConfigError
from invenio_cli.helpers.cli_config import CLIConfig


def test_cli_config_write():
    """Check config file is generated: preliminary superficial test."""
    tmp_dir = tempfile.TemporaryDirectory()
    project_dir = tmp_dir.name
    flavour = "RDM"
    replay = {
        "cookiecutter": {
            "project_name": "My Site",
            "project_shortname": "my-site",
            "project_site": "my-site.com",
            "github_repo": "my-site/my-site",
            "description": "Invenio RDM My Site Instance",
            "author_name": "CERN",
            "author_email": "info@my-site.com",
            "year": "2022",
            "database": "postgresql",
            "search": "opensearch1",
            "_template": "https://github.com/inveniosoftware/cookiecutter-invenio-rdm.git",  # noqa
        }
    }
    config_path = Path(project_dir) / CLIConfig.CONFIG_FILENAME
    private_config_path = Path(project_dir) / CLIConfig.PRIVATE_CONFIG_FILENAME

    # No configuration files
    assert not config_path.is_file()
    assert not private_config_path.is_file()

    CLIConfig.write(project_dir, flavour, replay)

    assert config_path.is_file()
    assert private_config_path.is_file()


@pytest.fixture
def config_dir():
    tmp_dir = tempfile.TemporaryDirectory()
    project_dir = tmp_dir.name
    flavour = "RDM"
    replay = {
        "cookiecutter": {
            "project_name": "My Site",
            "project_shortname": "my-site",
            "project_site": "my-site.com",
            "github_repo": "my-site/my-site",
            "description": "Invenio RDM My Site Instance",
            "author_name": "CERN",
            "author_email": "info@my-site.com",
            "year": "2022",
            "database": "postgresql",
            "search": "opensearch1",
            "_template": "https://github.com/inveniosoftware/cookiecutter-invenio-rdm.git",  # noqa
        }
    }
    # Need to yield in order for tmp_dir to not be gc'ed and therefore the
    # temporary directory deleted
    yield CLIConfig.write(project_dir, flavour, replay)


def test_cli_config_dot_invenio_not_found():
    with pytest.raises(InvenioCLIConfigError):
        CLIConfig()


def test_cli_config_get_project_dir(config_dir):
    # implicit project directory
    test_dir = Path.cwd()
    os.chdir(config_dir)
    cli_config = CLIConfig()
    assert cli_config.get_project_dir() == Path.cwd().resolve()
    os.chdir(test_dir)

    # explicit project directory
    cli_config = CLIConfig(config_dir)
    assert cli_config.get_project_dir() == config_dir


def test_cli_config_instance_path(config_dir):
    cli_config = CLIConfig(config_dir)

    with pytest.raises(InvenioCLIConfigError):
        cli_config.get_instance_path()

    # Update instance path to now see if we retrieve it
    instance_path = config_dir / ".venv/"
    cli_config.update_instance_path(instance_path)
    assert cli_config.get_instance_path() == Path(instance_path)


def test_cli_config_services_setup(config_dir):
    cli_config = CLIConfig(config_dir)

    assert cli_config.get_services_setup() is False

    cli_config.update_services_setup(True)

    assert cli_config.get_services_setup() is True


def test_cli_config_get_project_shortname(config_dir):
    cli_config = CLIConfig(config_dir)

    assert cli_config.get_project_shortname() == "my-site"


@pytest.mark.parametrize(
    "package_manager, expected_in_cli",
    [
        ("pnpm", True),
        ("npm", False),
        (None, False),
    ],
)
def test_javascript_package_manager_config(package_manager, expected_in_cli, tmpdir):
    """Test JavaScript package manager is correctly set in CLI config."""
    project_dir = tmpdir.mkdir("test-project")
    flavour = "RDM"
    replay = {
        "cookiecutter": {
            "project_name": "My Site",
            "project_shortname": "my-site",
            "project_site": "my-site.com",
            "github_repo": "my-site/my-site",
            "description": "Invenio RDM My Site Instance",
            "author_name": "CERN",
            "author_email": "info@my-site.com",
            "year": "2022",
            "database": "postgresql",
            "search": "opensearch1",
            "_template": "https://github.com/inveniosoftware/cookiecutter-invenio-rdm.git",  # noqa
        }
    }
    if package_manager is not None:
        replay["cookiecutter"]["javascript_package_manager"] = package_manager

    CLIConfig.write(str(project_dir), flavour, replay)

    config = ConfigParser()
    config_path = project_dir.join(CLIConfig.CONFIG_FILENAME)
    config.read(str(config_path))

    if expected_in_cli:
        assert config.has_option(CLIConfig.CLI_SECTION, "javascript_package_manager")
        assert config.get(CLIConfig.CLI_SECTION, "javascript_package_manager") == "pnpm"
    else:
        assert not config.has_option(
            CLIConfig.CLI_SECTION, "javascript_package_manager"
        )
