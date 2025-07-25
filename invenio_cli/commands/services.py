# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
# Copyright (C) 2021 Esteban J. G. Gabancho.
# Copyright (C) 2024 Graz University of Technology.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import click

from invenio_cli.commands.translations import TranslationsCommands
from invenio_cli.helpers.env import env

from ..helpers.docker_helper import DockerHelper
from ..helpers.process import ProcessResponse
from ..helpers.versions import ils_version, rdm_version
from .commands import Commands
from .services_health import HEALTHCHECKS, ServicesHealthCommands
from .steps import CommandStep, FunctionStep


class ServicesCommands(Commands):
    """Service CLI commands."""

    def __init__(self, cli_config, docker_helper=None):
        """Constructor."""
        super().__init__(cli_config)
        self.docker_helper = docker_helper or DockerHelper(
            cli_config.get_project_shortname(), local=True
        )

    def ensure_containers_running(self):
        """Ensures containers are running."""
        project_shortname = self.cli_config.get_project_shortname()

        cmd_env = {}
        instance_path = self.cli_config.get_instance_path(throw=False)
        if instance_path:
            cmd_env = {"INSTANCE_PATH": str(instance_path)}
        # Set environment variable for the instance path, it might be needed by docker services
        with env(**cmd_env):
            self.docker_helper.start_containers()

        services = ["redis", self.cli_config.get_db_type(), "search"]
        for service in services:
            ready = ServicesHealthCommands.wait_for_service(
                service,
                project_shortname=project_shortname,
                print_func=lambda msg: click.secho(msg, fg="yellow"),
                search_host=self.cli_config.get_search_host(),
                search_port=self.cli_config.get_search_port(),
            )

            if not ready:
                return ProcessResponse(
                    error=f"Unable to boot up {service}",
                    status_code=1,
                )
            else:
                # We should not use `click` outside the `cli` context, but
                # the return signature of this method does not support a list
                # of `ProcessResponse` objs, so it is printed directly here.
                click.secho(f"{service} up and running!", fg="green")

        return ProcessResponse(
            output="Containers started and healthy.",
            status_code=0,
        )

    def services_expected_status(self, expected):
        """Checks if the services have the expected status."""
        if not self.cli_config.get_services_setup() == expected:
            return ProcessResponse(
                error="Services status inconsistent."
                + f"Expected {expected} obtained {not expected}",
                status_code=1,
            )

        return ProcessResponse(
            output="Services setup status consistent.", status_code=0
        )

    def _cleanup(self):
        """Services cleanup steps."""
        pkg_man = self.cli_config.python_package_manager
        steps = [
            CommandStep(
                cmd=pkg_man.run_command(
                    "invenio",
                    "shell",
                    "--no-term-title",
                    "-c",
                    "import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')",  # noqa
                ),
                env={"PIPENV_VERBOSITY": "-1"},
                message="Flushing Redis...",
                skippable=True,
            ),
            CommandStep(
                cmd=pkg_man.run_command("invenio", "db", "destroy", "--yes-i-know"),
                env={"PIPENV_VERBOSITY": "-1"},
                message="Destroying database...",
                skippable=True,
            ),
            CommandStep(
                cmd=pkg_man.run_command(
                    "invenio",
                    "index",
                    "destroy",
                    "--force",
                    "--yes-i-know",
                ),
                env={"PIPENV_VERBOSITY": "-1"},
                message="Destroying indices...",
                skippable=True,
            ),
            CommandStep(
                cmd=pkg_man.run_command("invenio", "index", "queue", "init", "purge"),
                env={"PIPENV_VERBOSITY": "-1"},
                message="Purging queues...",
                skippable=True,
            ),
            FunctionStep(
                func=self.cli_config.update_services_setup,
                args={"is_setup": False},
                message="Updating service setup status (False)...",
            ),
        ]

        return steps

    def _default_location_path(self):
        """Build default location path based on file storage selection."""
        file_storage = self.cli_config.get_file_storage()
        if file_storage == "local":
            return "{}/data".format(self.cli_config.get_instance_path())
        return "{}://default".format(self.cli_config.get_file_storage().lower())

    def _setup(self, demo_data=False):
        """Services initialization steps."""
        pkg_man = self.cli_config.python_package_manager
        steps = [
            FunctionStep(
                func=self.services_expected_status,
                args={"expected": False},
                message="Checking services are not setup...",
            ),
            CommandStep(
                cmd=pkg_man.run_command("invenio", "db", "init", "create"),
                env={"PIPENV_VERBOSITY": "-1"},
                message="Creating database...",
            ),
            CommandStep(
                cmd=pkg_man.run_command(
                    "invenio",
                    "files",
                    "location",
                    "create",
                    "--default",
                    "default-location",
                    self._default_location_path(),
                ),
                env={"PIPENV_VERBOSITY": "-1"},
                message="Creating files location...",
            ),
            CommandStep(
                cmd=pkg_man.run_command("invenio", "roles", "create", "admin"),
                env={"PIPENV_VERBOSITY": "-1"},
                message="Creating admin role...",
            ),
            CommandStep(
                cmd=pkg_man.run_command(
                    "invenio",
                    "access",
                    "allow",
                    "superuser-access",
                    "role",
                    "admin",
                ),
                env={"PIPENV_VERBOSITY": "-1"},
                message="Allowing superuser access to admin role...",
            ),
            CommandStep(
                cmd=pkg_man.run_command("invenio", "index", "init"),
                env={"PIPENV_VERBOSITY": "-1"},
                message="Creating indices...",
            ),
        ]

        rdm_version_value = rdm_version()
        if rdm_version_value:
            if rdm_version_value[0] >= 10:
                steps.extend(
                    [
                        CommandStep(
                            cmd=pkg_man.run_command(
                                "invenio",
                                "rdm-records",
                                "custom-fields",
                                "init",
                            ),
                            env={"PIPENV_VERBOSITY": "-1"},
                            message="Creating custom fields for records...",
                        ),
                        CommandStep(
                            cmd=pkg_man.run_command(
                                "invenio",
                                "communities",
                                "custom-fields",
                                "init",
                            ),
                            env={"PIPENV_VERBOSITY": "-1"},
                            message="Creating custom fields for communities...",
                        ),
                    ]
                )

            if rdm_version_value[0] >= 11:
                steps.extend(self.rdm_fixtures())
                steps.extend(self.translations())

            if rdm_version_value[0] >= 12:
                steps.extend(self.declare_queues())

            steps.extend(self.fixtures())
            if demo_data:
                steps.extend(self.demo())
        else:
            click.secho(
                "RDM version couldn't be determined. RDM-specific steps will not be executed.",
                fg="yellow",
                err=True,
            )

        if ils_version():
            cmd = pkg_man.run_command("invenio", "setup", "--verbose")
            if not demo_data:
                cmd.append("--skip-demo-data")
            steps.extend(
                [
                    CommandStep(
                        cmd=cmd,
                        env={"PIPENV_VERBOSITY": "-1"},
                        message="Setting up services...",
                    )
                ]
            )

        steps.append(
            FunctionStep(
                func=self.cli_config.update_services_setup,
                args={"is_setup": True},
                message="Updating service setup status (True)...",
            ),
        )

        return steps

    def demo(self):
        """Steps to add demo records into the instance."""
        pkg_man = self.cli_config.python_package_manager
        steps = [
            CommandStep(
                cmd=pkg_man.run_command("invenio", "rdm-records", "demo"),
                env={"PIPENV_VERBOSITY": "-1"},
                message="Creating demo records...",
            )
        ]

        return steps

    def declare_queues(self):
        """Steps to declare the MQ queues required for statistics, etc."""
        pkg_man = self.cli_config.python_package_manager
        command = pkg_man.run_command("invenio", "queues", "declare")
        steps = [CommandStep(cmd=command, message="Declaring queues...")]
        return steps

    def fixtures(self):
        """Steps to set up the required fixtures for the instance."""
        pkg_man = self.cli_config.python_package_manager
        command = pkg_man.run_command("invenio", "rdm-records", "fixtures")
        steps = [
            CommandStep(
                cmd=command,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Creating records fixtures...",
            )
        ]

        return steps

    def rdm_fixtures(self):
        """Steps to set up the rdm fixtures for the instance."""
        pkg_man = self.cli_config.python_package_manager
        command = pkg_man.run_command("invenio", "rdm", "fixtures")
        steps = [
            CommandStep(
                cmd=command,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Creating rdm fixtures...",
            )
        ]

        return steps

    def translations(self):
        """Steps to compile translations."""
        commands = TranslationsCommands(
            self.cli_config,
            project_path=self.cli_config.get_project_dir(),
            instance_path=self.cli_config.get_instance_path(),
        )
        return commands.compile(symlink=False)

    def setup(self, force, demo_data=True, stop=False, services=True):
        """Steps to setup services' containers.

        A check in invenio-cli's config file is done to see if one-time setup
        has been executed before.
        """
        steps = []

        if services:
            steps.append(
                FunctionStep(
                    func=self.ensure_containers_running,
                    message="Making sure containers are up...",
                )
            )
        if force:
            steps.extend(self._cleanup())

        steps.extend(self._setup(demo_data))

        if stop:
            steps.append(
                FunctionStep(
                    func=self.docker_helper.stop_containers,
                    message="Stopping containers....",
                )
            )
        return steps

    def start(self):
        """Steps to start services' containers."""
        steps = [
            FunctionStep(
                func=self.ensure_containers_running,
                message="Making sure containers are up...",
            )
        ]

        return steps

    def stop(self):
        """Stops containers."""
        steps = [
            FunctionStep(
                func=self.docker_helper.stop_containers,
                message="Stopping containers...",
            )
        ]

        return steps

    def destroy(self):
        """Steps to destroy the services's containers."""
        steps = [
            FunctionStep(
                func=self.docker_helper.destroy_containers,
                message="Destroying containers...",
            ),
            FunctionStep(
                func=self.cli_config.update_services_setup,
                args={"is_setup": False},
                message="Updating service setup status (False)...",
            ),
        ]

        return steps

    def status(self, services, verbose):
        """Checks the status of the given service.

        :returns: A list of the same length than services. Each item will be a
                  code corresponding to: 0 success, 1 failure, 2 healthcheck
                  not defined.
        """
        project_shortname = self.cli_config.get_project_shortname()
        statuses = []
        for service in services:
            check = HEALTHCHECKS.get(service)
            if check:
                check_func = check["func"]
                response = check_func(
                    filepath="docker-services.yml",
                    verbose=verbose,
                    project_shortname=project_shortname,
                    search_host=self.cli_config.get_search_host(),
                    search_port=self.cli_config.get_search_port(),
                )
                # Append 0 if OK, else 1
                # FIXME: Deal with codes higher than 1. Needed?
                code = 0 if response.status_code == 0 else 1
                statuses.append((service, code))
            else:
                statuses.append((service, None))

        return statuses
