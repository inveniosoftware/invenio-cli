# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2022-2025 Graz University of Technology.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import os
import signal
import sys
from distutils.dir_util import copy_tree
from os import environ, symlink
from pathlib import Path
from shutil import copyfile
from subprocess import Popen as popen

import click

from ..helpers import env, filesystem
from ..helpers.process import ProcessResponse, run_interactive
from .commands import Commands


class LocalCommands(Commands):
    """Local CLI commands."""

    def __init__(self, cli_config):
        """Constructor."""
        super().__init__(cli_config)

    def _symlink_assets_templates(self, *args, **kwargs):
        """Symlink the assets folder."""
        files_to_link = self._copied_files
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
            self._copied_files = copy_tree(src_dir, dst_dir)
        self._copied_files = []

    def _symlink_locked_file(self):
        """Symlink locked file."""
        instance_path = self.cli_config.get_instance_path()
        project_dir = self.cli_config.get_project_dir()

        if self.cli_config.javascript_packages_manager == "npm":
            lock_file = "packages-lock.json"
        elif self.cli_config.javascript_packages_manager == "pnpm":
            lock_file = "pnpm-lock.yaml"

        source_path = project_dir / lock_file
        target_path = instance_path / "assets" / lock_file

        if Path(source_path).exists():
            symlink(source_path, target_path)

    def _cache_locked_file(self):
        """Cache locked file."""
        instance_path = self.cli_config.get_instance_path()
        project_dir = self.cli_config.get_project_dir()

        if self.cli_config.javascript_packages_manager == "npm":
            lock_file = "packages-lock.json"
        elif self.cli_config.javascript_packages_manager == "pnpm":
            lock_file = "pnpm-lock.yaml"

        target_path = project_dir / lock_file
        source_path = instance_path / "assets" / lock_file
        if not source_path.is_symlink():
            copyfile(source_path, target_path)

    def _statics(self, *args, **kwargs):
        # Symlink the instance's statics and assets
        copied_files = self._copy_statics_and_assets()
        self._symlink_assets_templates(copied_files)
        return ProcessResponse(
            output="Assets and statics updated.",
            status_code=0,
        )

    def update_statics_and_assets(
        self, force, debug=False, log_file=None, re_lock=True
    ):
        """High-level command to update less/js/images/... files.

        Needed here (parent) because is used by Assets and Install commands.
        """
        # Commands
        if self.cli_config.python_packages_manager == "uv":
            prefix = ["uv", "run", "invenio"]
        elif self.cli_config.python_packages_manager == "pip":
            prefix = ["pipenv", "run", "invenio"]
        else:
            print("please configure python package manager.")
            sys.exit()

        ops = [prefix + ["collect", "--verbose"]]

        if force:
            ops.append(prefix + ["webpack", "clean", "create"])
            ops.append(prefix + ["webpack", "install"])
        else:
            ops.append(prefix + ["webpack", "create"])
        ops.append(self._statics)
        ops.append(prefix + ["webpack", "build"])
        # Keep the same messages for some of the operations for backward compatibility
        messages = {
            "build": "Building assets...",
            "install": "Installing JS dependencies...",
        }

        with env(FLASK_DEBUG="true"):
            for op in ops:
                if callable(op):
                    response = op()
                else:
                    if op[-1] in messages:
                        click.secho(messages[op[-1]], fg="green")
                    response = run_interactive(
                        op,
                        env={"PIPENV_VERBOSITY": "-1"},
                        log_file=log_file,
                    )
                if response.status_code != 0:
                    break
        return response

    def lock(self):
        """Lock javascript dependencies."""
        from flask_collect import Collect
        from invenio_app.factory import create_app

        # takes around 4 seconds
        # the app is mainly used to set up the blueprints, therefore difficult to remove the creation
        app = create_app()
        app.config.setdefault(
            "JAVASCRIPT_PACKAGES_MANAGER", self.cli_config.javascript_packages_manager
        )
        app.config.setdefault("ASSETS_BUILDER", self.cli_config.assets_builder)

        collect = Collect(app)

        project = app.extensions["invenio-assets"].project
        project.app = app

        collect.collect(verbose=True)

        project.clean()
        project.create()

        project.install("--lockfile-only")

        self._cache_locked_file()

        return ProcessResponse(output="Assets locked", status_code=0)

    def _handle_sigint(self, name, process):
        """Terminate services on SIGINT."""
        prev_handler = signal.getsignal(signal.SIGINT)

        def _signal_handler(sig, frame):
            click.secho(f"Stopping {name}...", fg="green")
            process.terminate()
            click.secho(f"{name} stopped...", fg="green")
            if prev_handler is not None:
                prev_handler(sig, frame)

        signal.signal(signal.SIGINT, _signal_handler)

    def run_web(self, host, port, debug=True):
        """Run development server."""
        click.secho("Starting up local (development) server...", fg="green")
        run_env = environ.copy()
        run_env["FLASK_DEBUG"] = str(debug)
        run_env["INVENIO_SITE_UI_URL"] = f"https://{host}:{port}"
        run_env["INVENIO_SITE_API_URL"] = f"https://{host}:{port}/api"
        proc = popen(
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
        self._handle_sigint("Web server", proc)
        click.secho(f"Instance running!\nVisit https://{host}:{port}", fg="green")
        return [proc]

    def run_worker(self, celery_log_file=None, celery_log_level="INFO"):
        """Run Celery worker."""
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
            celery_log_level,
            "--queues",
            "celery,low",
        ]

        if celery_log_file:
            celery_command += [
                "--logfile",
                celery_log_file,
            ]

        proc = popen(celery_command)
        self._handle_sigint("Celery worker", proc)
        click.secho("Worker running!", fg="green")
        return [proc]

    def run_all(
        self,
        host,
        port,
        debug=True,
        services=True,
        celery_log_file=None,
        celery_log_level="INFO",
    ):
        """Run all services."""
        return [
            *self.run_web(host, port, debug),
            *self.run_worker(celery_log_file, celery_log_level),
        ]
