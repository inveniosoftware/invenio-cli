# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""


import os
import site
import sys
from pathlib import Path

from ..helpers import filesystem
from ..helpers.process import ProcessResponse
from .local import LocalCommands
from .packages import PackagesCommands
from .steps import FunctionStep


def reload_editable_package(item):
    """Reload editable packages.

    Manually process a .pth file to add paths to sys.path or execute import
    statements. Only necessary on the install step, because assets build doesn't
    know the previously install packages
    """
    with Path(item).open("r") as pth_file:
        for line in pth_file:
            line = line.strip()

            if line.startswith("import"):
                exec(line)
            elif os.path.isdir(line) and line not in sys.path:
                sys.path.insert(0, line)


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
        # https://github.com/inveniosoftware/invenio-app/blob/master/invenio_app/factory.py#L34
        # a problem is INVENIO_INSTANCE_PATH is set to not default!
        # maybe give possibility to override via click command!
        instance_path = f"{sys.prefix}/var/instance"
        self.cli_config.update_instance_path(instance_path)

        try:
            os.makedirs(instance_path)
        except FileExistsError:
            pass

        return ProcessResponse(
            output="Instance path updated successfully.", status_code=0
        )

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

    def install_assets(self, flask_env="production"):
        """Install assets."""
        return [
            FunctionStep(
                func=self.reload_editable_packages,
                message="Reload editable packages",
            ),
            FunctionStep(
                func=self.update_statics_and_assets,
                args={"force": True, "flask_env": flask_env},
                message="Updating statics and assets...",
            ),
        ]

    def install(self, pre, dev=False, flask_env="production"):
        """Development installation steps."""
        steps = []
        steps.extend(self.install_py_dependencies(pre=pre, dev=dev))
        steps.extend(self.symlink())
        steps.extend(self.install_assets(flask_env))
        return steps
