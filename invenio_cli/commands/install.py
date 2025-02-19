# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2024-2025 Graz University of Technology.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""


import os
import site
from contextlib import suppress

from ..errors import InvenioCLIConfigError
from ..helpers import filesystem
from ..helpers.process import ProcessResponse, run_cmd
from .commands import reload_editable_package
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
        packages_commands = PackagesCommands(self.cli_config)

        if packages_commands.is_locked().status_code > 0:
            steps.extend(packages_commands.lock(pre, dev))

        steps.extend(packages_commands.install_locked_dependencies(pre, dev))

        return steps

    def update_instance_path(self):
        """Update path to instance in config."""
        try:
            instance_path = self.cli_config.get_instance_path()

            with suppress(FileExistsError):
                os.makedirs(instance_path)

            return ProcessResponse(output="Instance path already set.", status_code=0)
        except InvenioCLIConfigError:
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
                func=self.update_instance_path,
                message="Updating instance path...",
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

    def reload_editable_packages(self):
        """Reload editable packages."""
        site_packages = site.getsitepackages()

        for site_package in site_packages:
            for item in os.listdir(site_package):
                if item.startswith("__editable__") and item.endswith(".pth"):
                    reload_editable_package(site_package + "/" + item)

        return ProcessResponse(
            output="Reloaded successfully editable packages.", status_code=0
        )

    def install_assets(self, debug=False, re_lock=True):
        """Install assets."""
        return [
            FunctionStep(
                func=self.reload_editable_packages,
                message="Reload editable packages",
            ),
            FunctionStep(
                func=self.update_statics_and_assets,
                args={"force": True, "debug": debug, "re_lock": re_lock},
                message="Updating statics and assets...",
            ),
        ]

    def install(self, pre, dev=False, debug=False, re_lock=True):
        """Development installation steps."""
        steps = []
        steps.extend(self.install_py_dependencies(pre=pre, dev=dev))
        steps.extend(self.symlink())
        steps.extend(self.install_assets(debug, re_lock))
        return steps
