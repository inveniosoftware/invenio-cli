# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2022 Graz University of Technology.
# Copyright (C) 2025 TUBITAK ULAKBIM
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

from ..helpers import env, filesystem
from ..helpers.process import ProcessResponse, run_interactive
from ..helpers.versions import rdm_version
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

    def update_statics_and_assets(self, force, debug=False, log_file=None):
        """High-level command to update less/js/images/... files.

        Needed here (parent) because is used by Assets and Install commands.
        """
        # Commands
        py_pkg_man = self.cli_config.python_package_manager
        js_pkg_man = self.cli_config.javascript_package_manager
        ops = [py_pkg_man.run_command("invenio", "collect", "--verbose")]

        js_translations_bundle_path = self.cli_config.get_js_translations_bundle_path()
        ops.append(
            pkg_man.run_command(
                "invenio",
                "i18n",
                "distribute-js-translations",
                "-i",
                js_translations_bundle_path,
            )
        )

        if force:
            ops.append(py_pkg_man.run_command("invenio", "webpack", "clean", "create"))
            ops.append(py_pkg_man.run_command("invenio", "webpack", "install"))
        else:
            ops.append(py_pkg_man.run_command("invenio", "webpack", "create"))
        ops.append(self._statics)
        ops.append(py_pkg_man.run_command("invenio", "webpack", "build"))
        # Keep the same messages for some of the operations for backward compatibility
        messages = {
            "build": "Building assets...",
            "install": "Installing JS dependencies...",
        }

        with env(FLASK_DEBUG="1" if debug else "0"):
            for op in ops:
                if callable(op):
                    response = op()
                else:
                    if op[-1] in messages:
                        click.secho(messages[op[-1]], fg="green")
                    response = run_interactive(
                        op,
                        env={"PIPENV_VERBOSITY": "-1", **js_pkg_man.env_overrides()},
                        log_file=log_file,
                    )
                if response.status_code != 0:
                    break
        return response

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
        run_env["FLASK_DEBUG"] = "1" if debug else "0"
        run_env["INVENIO_SITE_UI_URL"] = f"https://{host}:{port}"
        run_env["INVENIO_SITE_API_URL"] = f"https://{host}:{port}/api"
        pkg_man = self.cli_config.python_package_manager
        proc = popen(
            pkg_man.run_command(
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
            ),
            env=run_env,
        )
        self._handle_sigint("Web server", proc)
        click.secho(f"Instance running!\nVisit https://{host}:{port}", fg="green")
        return [proc]

    def run_worker(
        self, celery_log_file=None, celery_log_level="INFO", jobs_scheduler=True
    ):
        """Run Celery worker."""
        click.secho("Starting celery worker...", fg="green")

        pkg_man = self.cli_config.python_package_manager
        celery_command = pkg_man.run_command(
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
        )

        if celery_log_file:
            celery_command += [
                "--logfile",
                celery_log_file,
            ]

        processes = []
        proc = popen(celery_command)
        self._handle_sigint("Celery worker", proc)
        click.secho("Worker running!", fg="green")
        processes.append(proc)

        if jobs_scheduler:
            processes.extend(self.run_jobs_scheduler(celery_log_file, celery_log_level))

        return processes

    def run_jobs_scheduler(self, celery_log_file=None, celery_log_level="INFO"):
        """Run Celery beat scheduler for jobs."""
        # Jobs scheduler is only available in RDM v13+
        version = rdm_version()
        if version is None:
            click.secho(
                "RDM version couldn't be determined. Not running jobs scheduler.",
                fg="yellow",
                err=True,
            )
            return []
        elif version[0] < 13:
            return []

        click.secho("Starting jobs scheduler...", fg="green")

        pkg_man = self.cli_config.python_package_manager
        beat_command = pkg_man.run_command(
            "celery",
            "--app",
            "invenio_app.celery",
            "beat",
            "--scheduler",
            "invenio_jobs.services.scheduler:RunScheduler",
            "--loglevel",
            celery_log_level,
        )

        if celery_log_file:
            beat_command += [
                "--logfile",
                celery_log_file,
            ]

        proc = popen(beat_command)
        self._handle_sigint("Jobs scheduler", proc)
        click.secho("Jobs scheduler running!", fg="green")
        return [proc]

    def run_all(
        self,
        host,
        port,
        debug=True,
        services=True,
        celery_log_file=None,
        celery_log_level="INFO",
        jobs_scheduler=True,
    ):
        """Run all services."""
        processes = [
            *self.run_web(host, port, debug),
            *self.run_worker(
                celery_log_file, celery_log_level, jobs_scheduler=jobs_scheduler
            ),
        ]

        return processes
