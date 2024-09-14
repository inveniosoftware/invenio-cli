# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2022-2024 Graz University of Technology.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import os
import signal
from distutils.dir_util import copy_tree
from os import environ
from pathlib import Path
from subprocess import Popen as popen

import click
from flask_collect import Collect
from invenio_app.factory import create_cli
from invenio_assets.webpack import project

from ..helpers import filesystem
from ..helpers.process import ProcessResponse
from .commands import Commands


class LocalCommands(Commands):
    """Local CLI commands."""

    def __init__(self, cli_config):
        """Constructor."""
        super().__init__(cli_config)

    def _symlink_assets_templates(self, files_to_link):
        """Symlink the assets folder."""
        assets = "assets"
        click.secho("Symlinking {}...".format(assets), fg="green")

        instance_path = self.cli_config.get_instance_path()
        project_dir = self.cli_config.get_project_dir()
        for file_path in files_to_link:
            file_path = Path(file_path)
            relative_path = file_path.relative_to(instance_path)
            target_path = project_dir / relative_path
            filesystem.force_symlink(target_path, file_path)

    def _copy_statics_and_assets(self):
        """Copy project's statics and assets into instance dir."""
        click.secho("Copying project statics and assets...", fg="green")

        # static and assets folders do not exist in non-RDM contexts
        rdm_static_dir_exists = os.path.exists("static")
        rdm_assets_dir_exists = os.path.exists("assets")

        if rdm_static_dir_exists:
            static = "static"
            src_dir = self.cli_config.get_project_dir() / static
            src_dir = str(src_dir)  # copy_tree below doesn't accept Path objects
            dst_dir = self.cli_config.get_instance_path() / static
            dst_dir = str(dst_dir)
            # using it for a different purpose then intended but very useful
            copy_tree(src_dir, dst_dir)

        if rdm_assets_dir_exists:
            assets = "assets"
            src_dir = self.cli_config.get_project_dir() / assets
            src_dir = str(src_dir)
            dst_dir = self.cli_config.get_instance_path() / assets
            dst_dir = str(dst_dir)
            # The full path to the files that were copied is returned
            return copy_tree(src_dir, dst_dir)
        return []

    def _statics(self):
        # Symlink the instance's statics and assets
        copied_files = self._copy_statics_and_assets()
        self._symlink_assets_templates(copied_files)
        return ProcessResponse(
            output="Assets and statics updated.",
            status_code=0,
        )

    def update_statics_and_assets(self, force, flask_env="production", log_file=None):
        """High-level command to update less/js/images/... files.

        Needed here (parent) because is used by Assets and Install commands.
        """
        app = create_cli()
        project.app = app
        collect = Collect(app)
        collect.collect(verbose=True)
        project.clean()
        project.create()
        project.install()
        copied_files = self._copy_statics_and_assets()
        self._symlink_assets_templates(copied_files)
        project.build()

    def run(self, host, port, debug=True, services=True, celery_log_file=None):
        """Run development server and celery queue."""

        def signal_handler(sig, frame):
            click.secho("Stopping server and worker...", fg="green")
            server.terminate()
            if services:
                worker.terminate()
            click.secho("Server and worker stopped...", fg="green")

        signal.signal(signal.SIGINT, signal_handler)

        if services:
            click.secho("Starting celery worker...", fg="green")

            celery_command = [
                "pipenv",
                "run",
                "celery",
                "--app",
                "invenio_app.celery",
                "worker",
                "--beat",
                "--events",
                "--loglevel",
                "INFO",
            ]

            if celery_log_file:
                celery_command += [
                    "--logfile",
                    celery_log_file,
                ]

            worker = popen(celery_command)

        click.secho("Starting up local (development) server...", fg="green")
        run_env = environ.copy()
        run_env["FLASK_ENV"] = "development" if debug else "production"
        run_env["INVENIO_SITE_UI_URL"] = f"https://{host}:{port}"
        run_env["INVENIO_SITE_API_URL"] = f"https://{host}:{port}/api"
        server = popen(
            [
                "pipenv",
                "run",
                "invenio",
                "run",
                "--cert",
                "docker/nginx/test.crt",
                "--key",
                "docker/nginx/test.key",
                "--host",
                host,
                "--port",
                port,
                "--extra-files",
                "invenio.cfg",
            ],
            env=run_env,
        )

        click.secho(f"Instance running!\nVisit https://{host}:{port}", fg="green")
        server.wait()
