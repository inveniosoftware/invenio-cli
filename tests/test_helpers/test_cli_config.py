# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module config_file tests."""
import os
import tempfile
from configparser import ConfigParser
from pathlib import Path

import pytest

from invenio_cli.helpers.cli_config import CLIConfig


def test_cli_config_write():
    """Check config file is generated: preliminary superficial test."""

    tmp_dir = tempfile.TemporaryDirectory()
    project_dir = tmp_dir.name
    flavour = 'RDM'
    replay = {
        'cookiecutter': {
            'project_name': 'My Site',
            'project_shortname': 'my-site',
            'project_site': 'my-site.com',
            'github_repo': 'my-site/my-site',
            'description': 'Invenio RDM My Site Instance',
            'author_name': 'CERN',
            'author_email': 'info@my-site.com',
            'year': '2020',
            'database': 'postgresql',
            'elasticsearch': '7',
            '_template': 'https://github.com/inveniosoftware/cookiecutter-invenio-rdm.git'  # noqa
        }
    }

    # No configuration file
    assert not os.path.isfile(
        Path(project_dir) / CLIConfig.CONFIG_FILENAME
    )

    config_path = CLIConfig.write(project_dir, flavour, replay)

    assert os.path.isfile(config_path)


@pytest.fixture
def config_path():
    tmp_dir = tempfile.TemporaryDirectory()
    project_dir = tmp_dir.name
    flavour = 'RDM'
    replay = {
        'cookiecutter': {
            'project_name': 'My Site',
            'project_shortname': 'my-site',
            'project_site': 'my-site.com',
            'github_repo': 'my-site/my-site',
            'description': 'Invenio RDM My Site Instance',
            'author_name': 'CERN',
            'author_email': 'info@my-site.com',
            'year': '2020',
            'database': 'postgresql',
            'elasticsearch': '7',
            '_template': 'https://github.com/inveniosoftware/cookiecutter-invenio-rdm.git'  # noqa
        }
    }
    # Need to yield in order for tmp_dir to not be gc'ed and therefore the
    # temporary directory deleted
    yield CLIConfig.write(project_dir, flavour, replay)


def test_cli_config_get_project_dir(config_path):
    cli_config = CLIConfig(config_path)

    assert cli_config.get_project_dir() == Path(os.path.dirname(config_path))


def test_cli_config_get_instance_path(config_path):
    cli_config = CLIConfig(config_path)

    assert cli_config.get_instance_path() == Path('')

    # Update instance path to now see if we retrieve it
    instance_path = os.path.join(os.path.dirname(config_path), '.venv/')
    cli_config.update_instance_path(instance_path)

    assert cli_config.get_instance_path() == Path(instance_path)
