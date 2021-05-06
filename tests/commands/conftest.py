# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 Northwestern University.
# Copyright (C) 2021 Esteban J. G. Gabancho.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Commands tests fixtures."""

from pathlib import Path
from unittest.mock import Mock

import pytest


@pytest.fixture
def mock_cli_config():
    """Mock CLIConfig object."""
    class MockCLIConfig(object):
        def __init__(self):
            self.services_setup = False

        def get_project_dir(self):
            return Path('project_dir')

        def get_instance_path(self):
            return Path('instance_dir')

        def get_services_setup(self):
            return self.services_setup

        def update_services_setup(self, is_setup):
            self.services_setup = bool(is_setup)

        def get_project_shortname(self):
            return 'project-shortname'

        def get_db_type(self):
            return 'postgresql'

        def get_file_storage(self):
            return 'local'

    return MockCLIConfig()


@pytest.fixture(scope="function")
def mocked_pipe():
    """Mock success return subprocess pipe for popen."""
    mocked_pipe = Mock()
    attrs = {
        'communicate.return_value': (b'output', b'error'),
        'returncode': 0
    }
    mocked_pipe.configure_mock(**attrs)
    return mocked_pipe


@pytest.fixture()
def testpkg():
    """Test package.json file."""
    return str(Path(__file__).parent / 'testpkg')
