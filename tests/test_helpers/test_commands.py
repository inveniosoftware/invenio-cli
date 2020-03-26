# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module commands.py's tests."""
import os
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
def test_localcommands_install_py_dependencies(patched_subprocess):
    commands = LocalCommands(Mock())

    commands._install_py_dependencies(pre=True, lock=True)

    patched_subprocess.run.assert_any_call(
        ['pipenv', 'install', '--dev', '--pre'],
        check=True
    )

    commands._install_py_dependencies(pre=True, lock=False)

    patched_subprocess.run.assert_any_call(
        ['pipenv', 'install', '--dev', '--pre', '--skip-lock'],
        check=True
    )

    commands._install_py_dependencies(pre=False, lock=True)

    patched_subprocess.run.assert_any_call(
        ['pipenv', 'install', '--dev'],
        check=True
    )

    commands._install_py_dependencies(pre=False, lock=False)

    patched_subprocess.run.assert_any_call(
        ['pipenv', 'install', '--dev', '--skip-lock'],
        check=True
    )


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

    return FakeCLIConfig()


@patch('invenio_cli.helpers.filesystem.os')
def test_symlink_project_file_or_folder(patched_os, fake_cli_config):
    commands = LocalCommands(fake_cli_config)
    file = 'invenio.cfg'

    commands._symlink_project_file_or_folder(file)

    patched_os.symlink.assert_called_with(
        Path('project_dir/invenio.cfg'), Path('instance_dir/invenio.cfg'))

    folder = 'templates/'

    commands._symlink_project_file_or_folder(folder)

    patched_os.symlink.assert_called_with(
        Path('project_dir/templates'), Path('instance_dir/templates'))


@patch('invenio_cli.helpers.filesystem.os')
def test_localcommands_symlink_assets_templates(patched_os, fake_cli_config):
    commands = LocalCommands(fake_cli_config)
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
        call(['pipenv', 'run', 'invenio', 'collect', '--verbose'], check=True),
        call(['pipenv', 'run', 'invenio', 'webpack', 'create'], check=True),
        call(['pipenv', 'run', 'invenio', 'webpack', 'install'], check=True),
        call(['pipenv', 'run', 'invenio', 'webpack', 'build'], check=True),
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
        call(['pipenv', 'run', 'invenio', 'collect', '--verbose'], check=True),
        call(['pipenv', 'run', 'invenio', 'webpack', 'create'], check=True),
        call(['pipenv', 'run', 'invenio', 'webpack', 'build'], check=True)
    ]
    assert patched_subprocess.run.mock_calls == expected_calls


def test_localcommands_install():
    commands = LocalCommands(fake_cli_config)
    commands._install_py_dependencies = Mock()
    commands._update_instance_path = Mock()
    commands._symlink_project_file_or_folder = Mock()
    commands.update_statics_and_assets = Mock()

    commands.install(False, False)

    commands._install_py_dependencies.assert_called_with(False, False)
    commands._update_instance_path.assert_called()
    expected_symlink_calls = [
        call('invenio.cfg'),
        call('templates'),
        call('app_data')
    ]
    assert (
        commands._symlink_project_file_or_folder.mock_calls ==
        expected_symlink_calls
    )
    commands.update_statics_and_assets.assert_called_with(install=True)


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
            'pipenv', 'run', 'invenio', 'files', 'location', 'create',
            '--default', 'default-location', 'instance_dir/data'
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


@patch('invenio_cli.helpers.commands.subprocess')
@patch('invenio_cli.helpers.commands.time')
@patch('invenio_cli.helpers.commands.DockerHelper')
def test_localcommands_demo(
        patched_docker_helper, patched_time, patched_subprocess,
        fake_cli_config):
    commands = LocalCommands(fake_cli_config)

    commands.demo()

    patched_subprocess.run.assert_called_with(
        ['pipenv', 'run', 'invenio', 'rdm-records', 'demo'],
        check=True
    )


@patch('invenio_cli.helpers.commands.subprocess')
@patch('invenio_cli.helpers.commands.time')
@patch('invenio_cli.helpers.commands.DockerHelper')
def test_localcommands_run(
        patched_docker_helper, patched_time, patched_subprocess,
        fake_cli_config):
    commands = LocalCommands(fake_cli_config)

    commands.run()

    run_env = os.environ.copy()
    run_env['FLASK_ENV'] = 'development'
    expected_calls = [
        call([
            'pipenv', 'run', 'celery', 'worker', '--app', 'invenio_app.celery'
        ]),
        call([
            'pipenv', 'run', 'invenio', 'run', '--cert',
            'docker/nginx/test.crt', '--key', 'docker/nginx/test.key'
        ], env=run_env),
        call().wait()
    ]
    assert patched_subprocess.Popen.mock_calls == expected_calls


@patch('invenio_cli.helpers.commands.subprocess')
@patch('invenio_cli.helpers.commands.time')
@patch('invenio_cli.helpers.commands.DockerHelper')
def test_containerizedcommands_containerize(
        patched_docker_helper, patched_time, patched_subprocess,
        fake_cli_config):
    commands = ContainerizedCommands(fake_cli_config, patched_docker_helper())

    # Case: pre=False, force=False, install=True
    commands.containerize(pre=False, force=False, install=True)

    commands.docker_helper.start_containers.assert_called()
    expected_setup_calls = [
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
    assert (
        commands.docker_helper.execute_cli_command.mock_calls ==
        expected_setup_calls
    )

    # Case: pre=False, force=False, install=False
    commands.docker_helper.execute_cli_command.reset_mock()

    commands.containerize(pre=False, force=False, install=False)

    assert (
        call('project-shortname', 'invenio webpack install --unsafe') not in
        commands.docker_helper.execute_cli_command.mock_calls
    )

    # Case: pre=False, force=True, install=True
    commands.docker_helper.execute_cli_command.reset_mock()

    commands.containerize(pre=False, force=True, install=True)

    expected_force_calls = [
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
    assert commands.docker_helper.execute_cli_command.mock_calls == (
        expected_force_calls + expected_setup_calls
    )

    # Case: pre=True, force=True, install=True
    # Testing pre does not change the commands result.
    # Only the locking of the Pipfile. No need to test all combinations.
    commands.docker_helper.execute_cli_command.reset_mock()

    commands.containerize(pre=True, force=True, install=True)

    assert commands.docker_helper.execute_cli_command.mock_calls == (
        expected_force_calls + expected_setup_calls
    )


@patch('invenio_cli.helpers.commands.subprocess')
@patch('invenio_cli.helpers.commands.DockerHelper')
def test_containerizedcommands_update_statics_and_assets(
        patched_docker_helper, patched_subprocess, fake_cli_config):
    commands = ContainerizedCommands(fake_cli_config, patched_docker_helper())

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

    expected_copy2_calls = [
        call(
            'project_dir/static/.',
            '/opt/invenio/var/instance/static/'
        ),
        call(
            'project_dir/assets/.',
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


@patch('invenio_cli.helpers.commands.os')
@patch('invenio_cli.helpers.commands.subprocess')
@patch('invenio_cli.helpers.commands.DockerHelper')
def test_containerizedcommands_lock_python_dependencies(
        patched_docker_helper, patched_subprocess, patched_os,
        fake_cli_config):

    commands = ContainerizedCommands(fake_cli_config, patched_docker_helper())

    # Case: Need to lock the Pipfile
    patched_os.listdir = lambda *args, **kwargs: []
    commands._lock_python_dependencies(pre=False)

    patched_subprocess.run.assert_called_with(
        ['pipenv', 'lock'], check=True)

    commands._lock_python_dependencies(pre=True)

    patched_subprocess.run.assert_called_with(
        ['pipenv', 'lock', '--pre'], check=True)

    # Case: Pipfile.lock already exists
    patched_subprocess.run.reset_mock()
    patched_os.listdir = lambda *args, **kwargs: ['Pipfile.lock']

    commands._lock_python_dependencies(pre=False)

    patched_subprocess.run.assert_not_called()

    commands._lock_python_dependencies(pre=True)

    patched_subprocess.run.assert_not_called()


@patch('invenio_cli.helpers.commands.subprocess')
@patch('invenio_cli.helpers.commands.time')
@patch('invenio_cli.helpers.commands.DockerHelper')
def test_containerizedcommands_demo(
        patched_docker_helper, patched_time, patched_subprocess,
        fake_cli_config):
    commands = ContainerizedCommands(fake_cli_config, patched_docker_helper())

    commands.demo()

    assert (
        commands.docker_helper.execute_cli_command.mock_calls ==
        [call('project-shortname', 'invenio rdm-records demo')]
    )
