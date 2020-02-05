# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module commands.py's tests."""
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest

from invenio_cli.helpers.commands import Commands, ContainerizedCommands, \
    LocalCommands


def test_commands_delegates_to_environment():
    commands = Commands(Mock(), True)

    assert isinstance(commands.environment, LocalCommands)

    commands = Commands(Mock(), False)

    assert isinstance(commands.environment, ContainerizedCommands)


@patch('invenio_cli.helpers.commands.subprocess')
def test_localcommands_build_install_py_dependencies(patched_subprocess):
    commands = LocalCommands(Mock())

    commands._install_py_dependencies(pre=True, lock=True)

    patched_subprocess.run.assert_any_call(
        ['pipenv', 'install', '--dev', '--pre'])

    commands._install_py_dependencies(pre=True, lock=False)

    patched_subprocess.run.assert_any_call(
        ['pipenv', 'install', '--dev', '--pre', '--skip-lock'])

    commands._install_py_dependencies(pre=False, lock=True)

    patched_subprocess.run.assert_any_call(
        ['pipenv', 'install', '--dev'])

    commands._install_py_dependencies(pre=False, lock=False)

    patched_subprocess.run.assert_any_call(
        ['pipenv', 'install', '--dev', '--skip-lock'])


@patch('invenio_cli.helpers.commands.subprocess')
def test_localcommands_update_instance_path(patched_subprocess):
    cli_config = Mock()
    patched_subprocess.run.return_value = Mock(stdout='instance_dir')
    commands = LocalCommands(cli_config)

    commands._update_instance_path()

    patched_subprocess.run.assert_called_with(
        ['pipenv', 'run', 'invenio', 'shell', '--no-term-title',
            '-c', '"print(app.instance_path, end=\'\')"'],
        check=True, universal_newlines=True, stdout=patched_subprocess.PIPE
    )
    cli_config.update_instance_path.assert_called_with('instance_dir')


@pytest.fixture
def fake_cli_config():
    class FakeCLIConfig(object):
        def __init__(self):
            pass

        def get_project_dir(self):
            return Path('project_dir')

        def get_instance_path(self):
            return Path('instance_dir')

    return FakeCLIConfig()


@patch('invenio_cli.helpers.filesystem.os')
def test_localcommands_symlink_project_config(patched_os, fake_cli_config):
    commands = LocalCommands(fake_cli_config)

    commands._symlink_project_config()

    patched_os.symlink.assert_called_with(
        Path('project_dir/invenio.cfg'), Path('instance_dir/invenio.cfg'))


@patch('invenio_cli.helpers.filesystem.os')
def test_localcommands_symlink_templates(patched_os, fake_cli_config):
    commands = LocalCommands(fake_cli_config)

    commands._symlink_templates()

    patched_os.symlink.assert_called_with(
        Path('project_dir/templates'), Path('instance_dir/templates'))


@patch('invenio_cli.helpers.filesystem.os')
def test_localcommands_symlink_assets_templates(patched_os):
    class FakeCLIConfig(object):
        def __init__(self):
            pass

        def get_project_dir(self):
            return Path('project_dir')

        def get_instance_path(self):
            return Path('instance_dir')

    commands = LocalCommands(FakeCLIConfig())

    files_to_link = ['instance_dir/templates/template.js']

    commands._symlink_assets_templates(files_to_link)

    patched_os.symlink.assert_called_with(
        'project_dir/templates/template.js',
        'instance_dir/templates/template.js')


@patch('invenio_cli.helpers.commands.dir_util')
@patch('invenio_cli.helpers.commands.subprocess')
def test_localcommands_update_statics_and_assets(
        patched_subprocess, patched_dir_util, fake_cli_config):

    commands = LocalCommands(fake_cli_config)

    commands.update_statics_and_assets(install=True)

    expected_calls = [
        call(['pipenv', 'run', 'invenio', 'collect', '--verbose']),
        call(['pipenv', 'run', 'invenio', 'webpack', 'create']),
        call(['pipenv', 'run', 'invenio', 'webpack', 'install']),
        call(['pipenv', 'run', 'invenio', 'webpack', 'build']),
    ]
    assert patched_subprocess.run.mock_calls == expected_calls
    patched_dir_util.copy_tree.assert_any_call(
        'project_dir/static', 'instance_dir/static'
    )
    patched_dir_util.copy_tree.assert_any_call(
        'project_dir/assets', 'instance_dir/assets'
    )

    # Reset for install=False assertions
    patched_subprocess.run.reset_mock()

    commands.update_statics_and_assets(install=False)

    expected_calls = [
        call(['pipenv', 'run', 'invenio', 'collect', '--verbose']),
        call(['pipenv', 'run', 'invenio', 'webpack', 'create']),
        call(['pipenv', 'run', 'invenio', 'webpack', 'build'])
    ]
    assert patched_subprocess.run.mock_calls == expected_calls


@patch('invenio_cli.helpers.commands.subprocess')
@patch('invenio_cli.helpers.commands.time')
@patch('invenio_cli.helpers.commands.DockerHelper')
def test_localcommands_services(
        patched_docker_helper, patched_time, patched_subprocess,
        fake_cli_config):
    commands = LocalCommands(fake_cli_config)

    commands.services(force=False)

    expected_setup_calls = [
        call(['pipenv', 'run', 'invenio', 'db', 'init', 'create'], check=True),
        call([
            'pipenv', 'run', 'invenio', 'files', 'location', '--default',
            'default-location', 'instance_dir/data'
        ], check=True),
        call([
            'pipenv', 'run', 'invenio', 'roles', 'create', 'admin'
        ], check=True),
        call([
            'pipenv', 'run', 'invenio', 'access', 'allow',
            'superuser-access', 'role', 'admin'
        ], check=True),
        call(['pipenv', 'run', 'invenio', 'index', 'init'], check=True)
    ]
    assert patched_subprocess.run.mock_calls == expected_setup_calls

    # Reset for install=False assertions
    patched_subprocess.run.reset_mock()

    commands.services(force=True)

    expected_force_calls = [
        call([
            'pipenv', 'run', 'invenio', 'shell', '--no-term-title', '-c',
            "import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')"  # noqa
        ], check=True),
        call([
            'pipenv', 'run', 'invenio', 'db', 'destroy', '--yes-i-know',
        ], check=True),
        call([
            'pipenv', 'run', 'invenio', 'index', 'destroy', '--force',
            '--yes-i-know'
        ], check=True),
        call([
            'pipenv', 'run', 'invenio', 'index', 'queue', 'init', 'purge',
        ], check=True)
    ]
    assert patched_subprocess.run.mock_calls == (
            expected_force_calls + expected_setup_calls
    )
