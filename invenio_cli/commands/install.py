# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from ..helpers import env, filesystem
from ..helpers.process import run_cmd
from .local import LocalCommands
from .packages import PackagesCommands
from .steps import CommandStep, FunctionStep


class InstallCommands(LocalCommands):
    """Local installation commands."""

    def __init__(self, cli_config):
        """Constructor."""
        super(InstallCommands, self).__init__(cli_config)

    def install_py_dependencies(self, pre):
        """Install Python dependencies."""
        steps = [
            FunctionStep(
                func=PackagesCommands.is_locked,
                message="Checking if dependencies are locked."
            )
        ]
        steps.extend(PackagesCommands.install_locked_dependencies(pre))

        return steps

    def update_instance_path(self):
        """Update path to instance in config."""
        # FIXME: Transform into steps.
        # Currently not possible because the second step (update instance
        # path) requires the ouptut of the previous step
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

        steps = [
            FunctionStep(
                func=filesystem.force_symlink,
                args={"target": target_path, "link_name": link_path},
                message=f"Symlinking {target}..."
            )
        ]

        return steps

    def install(self, pre, flask_env='production'):
        """Development installation steps."""
        steps = self.install_py_dependencies(pre=pre)
        steps.append(
            FunctionStep(
                func=self.update_instance_path,
                message="Updating instance path..."
            )
        )
        steps.extend(self.symlink_project_file_or_folder('invenio.cfg'))
        steps.extend(self.symlink_project_file_or_folder('templates'))
        steps.extend(self.symlink_project_file_or_folder('app_data'))
        steps.append(
            FunctionStep(
                func=self.update_statics_and_assets,
                args={"force": True, "flask_env": flask_env},
                message="Creating symbolic link for app_data folder..."
            )
        )

        return steps
