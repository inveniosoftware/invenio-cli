# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module commands/local.py's tests."""

from os import environ
from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest
from click import UsageError

from invenio_cli.commands import LocalCommands


@pytest.mark.skip()
@patch('invenio_cli.commands.local.run_cmd')
def test_install_py_dependencies(p_run_cmd, mock_cli_config):
    commands = LocalCommands(mock_cli_config)

    commands._install_py_dependencies(pre=True, lock=True)

    p_run_cmd.assert_any_call(
        ['pipenv', 'install', '--dev', '--pre']
    )

    commands._install_py_dependencies(pre=True, lock=False)

    p_run_cmd.assert_any_call(
        ['pipenv', 'install', '--dev', '--pre', '--skip-lock']
    )

    commands._install_py_dependencies(pre=False, lock=True)

    p_run_cmd.assert_any_call(['pipenv', 'install', '--dev'])

    commands._install_py_dependencies(pre=False, lock=False)

    p_run_cmd.assert_any_call(
        ['pipenv', 'install', '--dev', '--skip-lock'],
    )


@pytest.mark.skip()
@patch('invenio_cli.commands.local.PIPE')
@patch('invenio_cli.commands.local.run_cmd')
def test_update_instance_path(p_run_cmd, p_PIPE):
    cli_config = Mock()
    p_run_cmd.return_value = Mock(stdout='instance_dir')
    commands = LocalCommands(cli_config)

    commands._update_instance_path()

    p_run_cmd.assert_called_with(
        ['pipenv', 'run', 'invenio', 'shell', '--no-term-title',
            '-c', '"print(app.instance_path, end=\'\')"'],
        check=True, universal_newlines=True, stdout=p_PIPE
    )
    cli_config.update_instance_path.assert_called_with('instance_dir')


@pytest.mark.skip()
@patch('invenio_cli.helpers.filesystem.symlink')
def test_symlink_project_file_or_folder(p_symlink, mock_cli_config):
    commands = LocalCommands(mock_cli_config)
    file = 'invenio.cfg'

    commands._symlink_project_file_or_folder(file)

    p_symlink.assert_called_with(
        Path('project_dir/invenio.cfg'), Path('instance_dir/invenio.cfg'))

    folder = 'templates/'

    commands._symlink_project_file_or_folder(folder)

    p_symlink.assert_called_with(
        Path('project_dir/templates'), Path('instance_dir/templates'))


@pytest.mark.skip()
@patch('invenio_cli.helpers.filesystem.symlink')
def test_symlink_assets_templates(p_symlink, mock_cli_config):
    commands = LocalCommands(mock_cli_config)
    files_to_link = ['instance_dir/templates/template.js']

    commands._symlink_assets_templates(files_to_link)

    p_symlink.assert_called_with(
        Path('project_dir/templates/template.js'),
        Path('instance_dir/templates/template.js')
    )


@pytest.mark.skip()
@patch('invenio_cli.commands.local.copy_tree')
@patch('invenio_cli.commands.local.run_cmd')
def test_update_statics_and_assets(p_run_cmd, p_copy_tree, mock_cli_config):
    commands = LocalCommands(mock_cli_config)
    commands.update_statics_and_assets(force=True)

    expected_calls = [
        call(['pipenv', 'run', 'invenio', 'collect', '--verbose']),
        call(['pipenv', 'run', 'invenio', 'webpack', 'clean', 'create']),
        call(['pipenv', 'run', 'invenio', 'webpack', 'install']),
        call(['pipenv', 'run', 'invenio', 'webpack', 'build']),
    ]
    assert p_run_cmd.mock_calls == expected_calls
    p_copy_tree.assert_any_call(
        'project_dir/static', 'instance_dir/static'
    )
    p_copy_tree.assert_any_call(
        'project_dir/assets', 'instance_dir/assets'
    )

    # Reset for install=False assertions
    p_run_cmd.reset_mock()

    commands.update_statics_and_assets(force=False)

    expected_calls = [
        call(['pipenv', 'run', 'invenio', 'collect', '--verbose']),
        call(['pipenv', 'run', 'invenio', 'webpack', 'create']),
        call(['pipenv', 'run', 'invenio', 'webpack', 'build'])
    ]
    assert p_run_cmd.mock_calls == expected_calls


@pytest.mark.skip()
@patch('invenio_cli.commands.local.run_cmd')
@patch('invenio_cli.commands.local.DockerHelper')
def test_watch(p_docker_helper, p_run_cmd, mock_cli_config):
    LocalCommands(mock_cli_config).watch_assets()

    p_run_cmd.assert_called_with(
        ['pipenv', 'run', 'invenio', 'webpack', 'run', 'start']
    )


@pytest.mark.skip()
def test_install(mock_cli_config):
    commands = LocalCommands(mock_cli_config)
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
    commands.update_statics_and_assets.assert_called_with(
        force=True, flask_env='production')


@pytest.mark.skip()
@patch('invenio_cli.commands.local.DockerHelper')
@patch('invenio_cli.commands.local.run_cmd')
@patch('invenio_cli.helpers.process.popen')
def test_services(
        p_popen, p_run_cmd, p_docker_helper, mock_cli_config, mocked_pipe):
    commands = LocalCommands(mock_cli_config)

    p_popen.return_value = mocked_pipe
    commands.services(force=False)

    expected_setup_calls = [
        call(['pipenv', 'run', 'invenio', 'db', 'init', 'create']),
        call([
            'pipenv', 'run', 'invenio', 'files', 'location', 'create',
            '--default', 'default-location', 'instance_dir/data'
        ]),
        call([
            'pipenv', 'run', 'invenio', 'roles', 'create', 'admin'
        ]),
        call([
            'pipenv', 'run', 'invenio', 'access', 'allow',
            'superuser-access', 'role', 'admin'
        ]),
        call(['pipenv', 'run', 'invenio', 'index', 'init'])
    ]
    assert p_run_cmd.mock_calls == expected_setup_calls

    # Reset for install=False assertions
    p_run_cmd.reset_mock()

    commands.services(force=True)

    expected_force_calls = [
        call([
            'pipenv', 'run', 'invenio', 'shell', '--no-term-title', '-c',
            "import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')"  # noqa
        ]),
        call([
            'pipenv', 'run', 'invenio', 'db', 'destroy', '--yes-i-know',
        ]),
        call([
            'pipenv', 'run', 'invenio', 'index', 'destroy', '--force',
            '--yes-i-know'
        ]),
        call([
            'pipenv', 'run', 'invenio', 'index', 'queue', 'init', 'purge',
        ])
    ]
    assert p_run_cmd.mock_calls == (
        expected_force_calls + expected_setup_calls
    )


@pytest.mark.skip()
@patch('invenio_cli.commands.local.run_cmd')
@patch('invenio_cli.commands.local.DockerHelper')
@patch('invenio_cli.helpers.process.popen')
def test_demo(
        p_popen, p_docker_helper, p_run_cmd, mock_cli_config, mocked_pipe):
    commands = LocalCommands(mock_cli_config)

    p_popen.return_value = mocked_pipe
    commands.demo()

    p_run_cmd.assert_called_with(
        ['pipenv', 'run', 'invenio', 'rdm-records', 'demo']
    )


@pytest.mark.skip()
@patch('invenio_cli.commands.local.DockerHelper')
@patch('invenio_cli.commands.local.run_cmd')
@patch('invenio_cli.commands.local.popen')
@patch('invenio_cli.helpers.process.popen')
def test_run(
        p_services_popen, p_commands_popen, p_run_cmd, p_docker_helper,
        mock_cli_config, mocked_pipe):
    commands = LocalCommands(mock_cli_config)
    p_services_popen.return_value = mocked_pipe

    host = '127.0.0.1'
    port = '5000'
    commands.run(host=host, port=port, debug=True)

    run_env = environ.copy()
    run_env['FLASK_ENV'] = 'development'
    run_env['INVENIO_SITE_HOSTNAME'] = f"{host}:{port}"
    expected_calls = [
        call([
            'pipenv', 'run', 'celery', '--app', 'invenio_app.celery', 'worker'
        ]),
        call([
            'pipenv', 'run', 'invenio', 'run', '--cert',
            'docker/nginx/test.crt', '--key', 'docker/nginx/test.key',
            '--host', '127.0.0.1', '--port', '5000'
        ], env=run_env),
        call().wait()
    ]
    assert p_commands_popen.mock_calls == expected_calls


@pytest.mark.skip()
@patch('pynpm.package.run_npm')
def test_link_js_module(p_run_npm, testpkg, mock_cli_config):

    LocalCommands(mock_cli_config).link_js_module(testpkg)

    expected_calls = [
        call(testpkg, 'run-script', npm_bin='npm', args=('link-dist',)),
        call('instance_dir/assets', 'link', npm_bin='npm', args=('testpkg',))
    ]

    assert expected_calls == p_run_npm.mock_calls


@pytest.mark.skip()
@patch('pynpm.package.run_npm')
def test_watch_js_module(p_run_npm, testpkg, mock_cli_config):

    LocalCommands(mock_cli_config).watch_js_module(
        testpkg, link=False)

    expected_calls = [
        call(testpkg, 'run-script', npm_bin='npm', args=('watch',)),
    ]
    assert expected_calls == p_run_npm.mock_calls


@pytest.mark.skip()
@patch('pynpm.package.run_npm')
def test_watch_js_module_w_build(p_run_npm, testpkg, mock_cli_config):

    LocalCommands(mock_cli_config).watch_js_module(testpkg, link=True)

    expected_calls = [
        call(testpkg, 'run-script', npm_bin='npm', args=('link-dist',)),
        call('instance_dir/assets', 'link', npm_bin='npm', args=('testpkg',)),
        call(testpkg, 'run-script', npm_bin='npm', args=('watch',)),
    ]
    assert expected_calls == p_run_npm.mock_calls


@pytest.mark.skip()
@patch('invenio_cli.commands.local.run_cmd')
def test_install_modules(p_run_cmd, mock_cli_config):
    commands = LocalCommands(mock_cli_config)

    """1 module"""
    modules = [Path().absolute()]
    commands.install_modules(modules)
    p_run_cmd.assert_called_with(
        ['pipenv', 'run', 'pip', 'install', '-e', modules[0]])

    """2 modules"""
    modules = [Path().absolute(), Path().absolute()]
    commands.install_modules(modules)
    p_run_cmd.assert_called_with(
        ['pipenv', 'run', 'pip', 'install', '-e', modules[0],
            '-e', modules[1]])

    """No modules"""
    modules = []
    with pytest.raises(UsageError):
        commands.install_modules(modules)
        cmd = ['pipenv', 'run', 'pip', 'install', '-e', modules]
        p_run_cmd(cmd)

    """Empty String"""
    """
    modules = [" "]
    with pytest.raises(click.UsageError):
        commands.install_modules(modules)
        cmd = ['invenio-cli', 'ext', 'module-install', modules[0]]
        print("comando")
        print(cmd)
        p_run_cmd(cmd)
    """

    """Invalid Path"""
    """
    modules = ["~/test/"]
    with pytest.raises(subprocess.CalledProcessError):
        commands.install_modules(modules)
        cmd = ['invenio-cli', 'ext', 'module-install', modules]
        p_run_cmd(cmd)
    """
