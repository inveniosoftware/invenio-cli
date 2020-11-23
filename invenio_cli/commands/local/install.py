# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""


from distutils.dir_util import copy_tree
from os import listdir
from pathlib import Path

import click

from ...helpers import env, filesystem
from ...helpers.process import ProcessResponse, run_cmd, run_interactive
from .local import LocalCommands


class InstallCommands(LocalCommands):
    """Local installation commands."""

    def __init__(self, cli_config):
        """Constructor."""
        super(InstallCommands, self).__init__(cli_config)

    def install_py_dependencies(self, pre):
        """Install Python dependencies."""
        locked = 'Pipfile.lock' in listdir('.')

        if not locked:
            return ProcessResponse(
                error="Dependencies were not locked. " +
                      "Please run `invenio-cli packages lock`.",
                status_code=1,
            )
        command = ['pipenv', 'sync']
        if pre:
            command += ['--pre']
        # NOTE: sync has not interactive process feedback
        result = run_cmd(command)
        result.output = "Python dependencies locked successfully."
        return result

    def update_instance_path(self):
        """Update path to instance in config."""
        result = run_cmd(
            ['pipenv', 'run', 'invenio', 'shell', '--no-term-title',
                '-c', '"print(app.instance_path, end=\'\')"']
        )
        self.cli_config.update_instance_path(result.output.strip())

        result.output = "Instance path successfully."
        return result

    def symlink_project_file_or_folder(self, target):
        """Create symlink in instance pointing to project file or folder."""
        target_path = self.cli_config.get_project_dir() / target
        link_path = self.cli_config.get_instance_path() / target
        filesystem.force_symlink(target_path, link_path)

        return ProcessResponse(
                output=f"{target} symlinked successfully.",
                status_code=0,
            )

    def _copy_statics_and_assets(self):
        """Copy project's statics and assets into instance dir."""
        click.secho('Copying project statics and assets...', fg='green')

        static = 'static'
        src_dir = self.cli_config.get_project_dir() / static
        src_dir = str(src_dir)  # copy_tree below doesn't accept Path objects
        dst_dir = self.cli_config.get_instance_path() / static
        dst_dir = str(dst_dir)
        # using it for a different purpose then intended but very useful
        copy_tree(src_dir, dst_dir)

        assets = 'assets'
        src_dir = self.cli_config.get_project_dir() / assets
        src_dir = str(src_dir)
        dst_dir = self.cli_config.get_instance_path() / assets
        dst_dir = str(dst_dir)
        # The full path to the files that were copied is returned
        copied_files = copy_tree(src_dir, dst_dir)
        return copied_files

    def _symlink_assets_templates(self, files_to_link):
        """Symlink the assets folder."""
        assets = 'assets'
        click.secho('Symlinking {}...'.format(assets), fg='green')

        instance_path = self.cli_config.get_instance_path()
        project_dir = self.cli_config.get_project_dir()
        for file_path in files_to_link:
            file_path = Path(file_path)
            relative_path = file_path.relative_to(instance_path)
            target_path = project_dir / relative_path
            filesystem.force_symlink(target_path, file_path)

    def install(self, pre, flask_env='production'):
        """Local build."""
        steps = [
            {
                "func": self.install_py_dependencies,
                "args": {"pre": pre},
                "message": "Installing python dependencies..." +
                           "Please be patient, " +
                           "this operation might take some time..."
            },
            {
                "func": self.update_instance_path,
                "args": {},
                "message": "Updating instance path..."
            },
            {
                "func": self.symlink_project_file_or_folder,
                "args": {"target": 'invenio.cfg'},
                "message": "Creating symbolic link for invenio.cfg..."
            },
            {
                "func": self.symlink_project_file_or_folder,
                "args": {"target": 'templates'},
                "message": "Creating symbolic link for templates folder..."
            },
            {
                "func": self.symlink_project_file_or_folder,
                "args": {"target": 'app_data'},
                "message": "Creating symbolic link for app_data folder..."
            },
            {
                "func": self.update_statics_and_assets,
                "args": {"force": True, "flask_env": flask_env},
                "message": "Creating symbolic link for app_data folder..."
            }
        ]

        for step in steps:
            click.secho(message=step.get("message"), fg="green")
            result = step.get("func")(**step.get("args"))
            if result.status_code > 0:
                return result
            else:
                click.secho(message=result.output, fg="green")

        return ProcessResponse(
            output="Successfully installed all dependencies.",
            status_code=0
        )

    def install_packages(self, modules):
        """Install Python packages."""
        if len(modules) < 1:
            raise click.UsageError("You must specify at least one package.")

        prefix = ['pipenv', 'run']
        cmd = prefix + ['pip', 'install']
        for module in modules:
            cmd.extend(['-e', module])

        return run_cmd(cmd)
