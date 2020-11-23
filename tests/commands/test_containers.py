# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module commands/containers.py's tests."""

from pathlib import Path
from unittest.mock import call, patch

import pytest

from invenio_cli.commands import ContainersCommands


@pytest.mark.skip()
@pytest.fixture(scope='function')
def expected_setup_calls():
    return [
        call('project-shortname', 'invenio db init create'),
        call(
            'project-shortname',
            'invenio files location create --default default-location '
            '${INVENIO_INSTANCE_PATH}/data'
        ),
        call('project-shortname', 'invenio roles create admin'),
        call(
            'project-shortname',
            'invenio access allow superuser-access role admin'
        ),
        call('project-shortname', 'invenio index init'),
        # update_statics_and_assets call
        call('project-shortname', 'invenio collect'),
        call('project-shortname', 'invenio webpack create'),
        call('project-shortname', 'invenio webpack install --unsafe'),
        call('project-shortname', 'invenio webpack build')
    ]


@pytest.mark.skip()
@pytest.fixture(scope='function')
def expected_force_calls():
    return [
        call(
            'project-shortname',
            "invenio shell --no-term-title -c "
            "\"import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')\""  # noqa
        ),
        call('project-shortname', 'invenio db destroy --yes-i-know'),
        call(
            'project-shortname',
            'invenio index destroy --force --yes-i-know'
        ),
        call('project-shortname', 'invenio index queue init purge')
    ]


@pytest.mark.skip()
@patch('invenio_cli.commands.containers.run_cmd')
@patch('invenio_cli.commands.containers.DockerHelper')
@patch('invenio_cli.helpers.process.popen')
def test_containerize_install(
        p_popen, p_docker_helper, p_run_cmd, mock_cli_config, mocked_pipe,
        expected_setup_calls):
    """Case: pre=False, force=False, install=True."""
    p_popen.return_value = mocked_pipe
    commands = ContainersCommands(mock_cli_config, p_docker_helper())
    commands.containerize(pre=False, force=False, install=True)

    commands.docker_helper.start_containers.assert_called()
    assert (
        commands.docker_helper.execute_cli_command.mock_calls ==
        expected_setup_calls
    )


@pytest.mark.skip()
@patch('invenio_cli.commands.containers.run_cmd')
@patch('invenio_cli.commands.containers.DockerHelper')
@patch('invenio_cli.helpers.process.popen')
def test_containerize_no_install(
        p_popen, p_docker_helper, p_run_cmd, mock_cli_config, mocked_pipe):
    """Case: pre=False, force=False, install=False"""
    p_popen.return_value = mocked_pipe
    commands = ContainersCommands(mock_cli_config, p_docker_helper())
    commands.docker_helper.execute_cli_command.reset_mock()

    commands.containerize(pre=False, force=False, install=False)

    assert (
        call('project-shortname', 'invenio webpack install --unsafe') not in
        commands.docker_helper.execute_cli_command.mock_calls
    )


@pytest.mark.skip()
@patch('invenio_cli.commands.containers.run_cmd')
@patch('invenio_cli.commands.containers.DockerHelper')
@patch('invenio_cli.helpers.process.popen')
def test_containerize_install_force(
        p_popen, p_docker_helper, p_run_cmd, mock_cli_config, mocked_pipe,
        expected_setup_calls, expected_force_calls):
    """Case: pre=False, force=True, install=True."""
    p_popen.return_value = mocked_pipe
    commands = ContainersCommands(mock_cli_config, p_docker_helper())
    commands.docker_helper.execute_cli_command.reset_mock()

    commands.containerize(pre=False, force=True, install=True)

    assert commands.docker_helper.execute_cli_command.mock_calls == (
        expected_force_calls + expected_setup_calls
    )


@pytest.mark.skip()
@patch('invenio_cli.commands.containers.run_cmd')
@patch('invenio_cli.commands.containers.DockerHelper')
@patch('invenio_cli.helpers.process.popen')
def test_containerize_install_pre_force(
        p_popen, p_docker_helper, p_run_cmd, mock_cli_config, mocked_pipe,
        expected_setup_calls, expected_force_calls):
    """Case: pre=True, force=True, install=True.
    Testing pre does not change the commands result.
    Only the locking of the Pipfile. No need to test all combinations.
    """
    p_popen.return_value = mocked_pipe
    commands = ContainersCommands(mock_cli_config, p_docker_helper())
    commands.docker_helper.execute_cli_command.reset_mock()
    commands.containerize(pre=True, force=True, install=True)

    assert commands.docker_helper.execute_cli_command.mock_calls == (
        expected_force_calls + expected_setup_calls
    )


@pytest.mark.skip()
@patch('invenio_cli.commands.containers.run_cmd')
@patch('invenio_cli.commands.containers.DockerHelper')
def test_update_statics_and_assets(
        p_docker_helper, p_run_cmd, mock_cli_config):
    commands = ContainersCommands(mock_cli_config, p_docker_helper())

    commands.update_statics_and_assets(install=True)

    expected_execute_cli_calls = [
        call('project-shortname', 'invenio collect'),
        call('project-shortname', 'invenio webpack create'),
        call('project-shortname', 'invenio webpack install --unsafe'),
        call('project-shortname', 'invenio webpack build')
    ]
    assert (
        commands.docker_helper.execute_cli_command.mock_calls ==
        expected_execute_cli_calls
    )

    # Second arg is str due to copy2 requirements
    expected_copy2_calls = [
        call(
            Path('project_dir/static/.'),
            '/opt/invenio/var/instance/static/'
        ),
        call(
            Path('project_dir/assets/.'),
            '/opt/invenio/var/instance/assets/'
        )
    ]
    assert commands.docker_helper.copy2.mock_calls == expected_copy2_calls

    # Reset for force=True assertions
    commands.docker_helper.execute_cli_command.reset_mock()

    commands.update_statics_and_assets(install=False)

    expected_execute_cli_calls = [
        call('project-shortname', 'invenio collect'),
        call('project-shortname', 'invenio webpack create'),
        call('project-shortname', 'invenio webpack build')
    ]
    assert (
        commands.docker_helper.execute_cli_command.mock_calls ==
        expected_execute_cli_calls
    )


@pytest.mark.skip()
@patch('invenio_cli.commands.containers.listdir', return_value=[])
@patch('invenio_cli.commands.containers.run_cmd')
@patch('invenio_cli.commands.containers.DockerHelper')
def test_lock_python_dependencies(
        p_docker_helper, p_run_cmd, p_listdir,
        mock_cli_config):
    commands = ContainersCommands(mock_cli_config, p_docker_helper())
    commands._lock_python_dependencies(pre=False)
    p_run_cmd.assert_called_with(['pipenv', 'lock'])

    commands._lock_python_dependencies(pre=True)

    p_run_cmd.assert_called_with(['pipenv', 'lock', '--pre'])


@pytest.mark.skip()
@patch('invenio_cli.commands.containers.listdir',
       return_value=['Pipfile.lock'])
@patch('invenio_cli.commands.containers.run_cmd')
@patch('invenio_cli.commands.containers.DockerHelper')
def test_no_lock_python_dependencies(
        p_docker_helper, p_run_cmd, p_listdir,
        mock_cli_config):
    commands = ContainersCommands(mock_cli_config, p_docker_helper())
    commands._lock_python_dependencies(pre=False)
    p_run_cmd.assert_not_called()

    commands._lock_python_dependencies(pre=True)
    p_run_cmd.assert_not_called()


@pytest.mark.skip()
@patch('invenio_cli.commands.containers.run_cmd')
@patch('invenio_cli.commands.containers.DockerHelper')
def test_demo(
        p_run_cmd, p_docker_helper, mock_cli_config):
    commands = ContainersCommands(mock_cli_config, p_docker_helper())

    commands.demo()

    assert (
        commands.docker_helper.execute_cli_command.mock_calls ==
        [call('project-shortname', 'invenio rdm-records demo')]
    )
