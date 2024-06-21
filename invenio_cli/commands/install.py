# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from ..helpers import filesystem
from ..helpers.process import run_cmd
from .local import LocalCommands
from .packages import PackagesCommands
from .steps import FunctionStep


class InstallCommands(LocalCommands):
    """Local installation commands."""

    def __init__(self, cli_config):
        """Constructor."""
        super().__init__(cli_config)

    def install_py_dependencies(self, pre, dev=False):
        """Install Python dependencies."""
        # If not locked, lock. Then install.
        steps = []

        if PackagesCommands.is_locked().status_code > 0:
            steps.extend(PackagesCommands.lock(pre, dev))

        steps.extend(PackagesCommands.install_locked_dependencies(pre, dev))

        return steps

    def update_instance_path(self):
        """Update path to instance in config."""
        # FIXME: Transform into steps.
        # Currently not possible because the second step (update instance
        # path) requires the ouptut of the previous step
        result = run_cmd(
            [
                "pipenv",
                "run",
                "invenio",
                "shell",
                "--no-term-title",
                "-c",
                "\"print(app.instance_path, end='')\"",
            ]
        )
        if result.status_code == 0:
            self.cli_config.update_instance_path(result.output.strip())
            result.output = "Instance path updated successfully."
        return result

    def _symlink_project_file_or_folder(self, target):
        """Create symlink in instance pointing to project file or folder."""
        target_path = self.cli_config.get_project_dir() / target
        link_path = self.cli_config.get_instance_path() / target

        return filesystem.force_symlink(target_path, link_path)

    def symlink(self):
        """Sylink all necessary project files and folders."""
        steps = []
        steps.append(
            FunctionStep(
                func=self.update_instance_path, message="Updating instance path..."
            )
        )

        paths = ("invenio.cfg", "templates", "app_data")
        steps.extend(
            [
                FunctionStep(
                    func=self._symlink_project_file_or_folder,
                    args={"target": path},
                    message=f"Symlinking '{path}'...",
                )
                for path in paths
            ]
        )
        return steps

    def install_assets(self, flask_env="production"):
        """Install assets."""
        return [
            FunctionStep(
                func=self.update_statics_and_assets,
                args={"force": True, "flask_env": flask_env},
                message="Updating statics and assets...",
            )
        ]

    def install(self, pre, dev=False, flask_env="production"):
        """Development installation steps."""
        steps = self.install_py_dependencies(pre=pre, dev=dev)
        steps.append(
            FunctionStep(
                func=self.update_instance_path, message="Updating instance path..."
            )
        )
        steps.extend(self.symlink())
        steps.extend(self.install_assets(flask_env))

        return steps
