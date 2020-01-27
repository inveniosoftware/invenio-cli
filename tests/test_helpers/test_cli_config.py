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
from pathlib import Path

from invenio_cli.helpers.cli_config import InvenioCLIConfig


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
        Path(project_dir) / InvenioCLIConfig.CONFIG_FILENAME
    )

    config_path = InvenioCLIConfig.write(project_dir, flavour, replay)

    assert os.path.isfile(config_path)
    # TODO: check content more thoroughly
    # InvenioCLIConfig.read
