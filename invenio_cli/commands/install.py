# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from ..helpers import filesystem
from ..helpers.packaging import get_packaging_backend
from ..helpers.process import run_cmd
from .local import LocalCommands
from .packages import PackagesCommands
from .steps import FunctionStep


class InstallCommands(LocalCommands):
    """Local installation commands."""

    def __init__(self, cli_config):
        """Constructor."""
        super(InstallCommands, self).__init__(cli_config)
        self.pkg_commands = PackagesCommands(cli_config)

    def install_py_dependencies(self, pre, dev=False):
        """Install Python dependencies."""
        # If not locked, lock. Then install.
        steps = []

        if self.pkg_commands.is_locked().status_code > 0:
            steps.extend(self.pkg_commands.lock(pre, dev))

        steps.extend(self.pkg_commands.install_locked_dependencies(pre, dev))

        return steps

    def update_instance_path(self):
        """Update path to instance in config."""
        # FIXME: Transform into steps.
        # Currently not possible because the second step (update instance
        # path) requires the ouptut of the previous step
        command = get_packaging_backend(self.cli_config).run_command(
            'invenio', 'shell', '--no-term-title', '-c',
            '"print(app.instance_path, end=\'\')"',
        )
        result = run_cmd(command)
        if result.status_code == 0:
            self.cli_config.update_instance_path(result.output.strip())
            result.output = "Instance path updated successfully."
        return result

    def symlink_project_file_or_folder(self, target):
        """Create symlink in instance pointing to project file or folder."""
        target_path = self.cli_config.get_project_dir() / target
        link_path = self.cli_config.get_instance_path() / target

        return filesystem.force_symlink(target_path, link_path)

    def install(self, pre, dev=False, flask_env='production'):
        """Development installation steps."""
        steps = self.install_py_dependencies(pre=pre, dev=dev)
        steps.append(
            FunctionStep(
                func=self.update_instance_path,
                message="Updating instance path..."
            )
        )
        steps.append(
            FunctionStep(
                func=self.symlink_project_file_or_folder,
                args={"target": 'invenio.cfg'},
                message="Symlinking 'invenio.cfg'..."
            )
            )
        steps.append(
            FunctionStep(
                func=self.symlink_project_file_or_folder,
                args={"target": 'templates'},
                message="Symlinking 'templates'..."
            )
            )
        steps.append(
            FunctionStep(
                func=self.symlink_project_file_or_folder,
                args={"target": 'app_data'},
                message="Symlinking 'app_data'..."
            )
        )
        steps.append(
            FunctionStep(
                func=self.update_statics_and_assets,
                args={"force": True, "flask_env": flask_env},
                message="Updating statics and assets..."
            )
        )

        return steps
