# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module commands/commands.py's tests."""

from unittest.mock import patch

import pytest

from invenio_cli.commands import Commands


@pytest.mark.skip()
# NOTE: The patch is the actual import without the `from <package>`
@patch('invenio_cli.helpers.process.run_cmd')
@patch('invenio_cli.commands.commands.DockerHelper')
def test_shell(p_docker_helper, p_run_cmd, mock_cli_config):
    Commands(mock_cli_config).shell()
    p_run_cmd.assert_called_with(['pipenv', 'shell'])


@pytest.mark.skip()
@patch('invenio_cli.helpers.process.run_cmd')
@patch('invenio_cli.commands.commands.DockerHelper')
def test_pyshell(p_docker_helper, p_run_cmd, mock_cli_config):
    Commands(mock_cli_config).pyshell()
    p_run_cmd.assert_called_with(['pipenv', 'run', 'invenio', 'shell'])


@pytest.mark.skip()
@patch('invenio_cli.commands.commands.DockerHelper')
def test_stop(p_docker_helper, mock_cli_config):
    commands = Commands(mock_cli_config, p_docker_helper())
    commands.stop()
    commands.docker_helper.stop_containers.assert_called()


@pytest.mark.skip()
@patch('invenio_cli.helpers.process.run_cmd')
@patch('invenio_cli.commands.commands.DockerHelper')
def test_destroy(p_docker_helper, p_run_cmd, mock_cli_config):
    commands = Commands(mock_cli_config, p_docker_helper())
    commands.destroy()

    p_run_cmd.assert_called_with(['pipenv', '--rm'])
    commands.docker_helper.destroy_containers.assert_called()
    assert mock_cli_config.services_setup is False
