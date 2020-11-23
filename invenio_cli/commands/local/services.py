# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from ...helpers.process import ProcessResponse, run_interactive
from .local import LocalCommands


class ServicesCommands(LocalCommands):

    def __init__(self, cli_config):
        """Constructor."""
        super(ServicesCommands, self).__init__(cli_config)

    def _cleanup(self):
        """Execute cleanup commands."""
        command = [
            'pipenv', 'run', 'invenio', 'shell', '--no-term-title', '-c',
            "import redis; redis.StrictRedis.from_url(app.config['CACHE_REDIS_URL']).flushall(); print('Cache cleared')"  # noqa
        ]
        run_interactive(command)

        # TODO: invenio-db#126 should make it idempotent
        command = [
            'pipenv', 'run', 'invenio', 'db', 'destroy', '--yes-i-know',
        ]
        run_interactive(command)

        # TODO: invenio-indexer#114 should make destroy and queue init
        #       purge idempotent
        command = [
            'pipenv', 'run', 'invenio', 'index', 'destroy',
            '--force', '--yes-i-know',
        ]
        run_interactive(command)

        command = [
            'pipenv', 'run', 'invenio', 'index', 'queue', 'init', 'purge']
        run_interactive(command)

        self.cli_config.update_services_setup(False)

    def _setup(self):
        """Initialize services."""
        command = ['pipenv', 'run', 'invenio', 'db', 'init', 'create']
        run_interactive(command)

        command = [
            'pipenv', 'run', 'invenio', 'files', 'location', 'create',
            '--default', 'default-location',
            "{}/data".format(self.cli_config.get_instance_path())
        ]
        run_interactive(command)

        # Without the self.cli_config.get_services_setup() check
        # this throws an error on re-runs
        # TODO: invenio-accounts#297 should make it idempotent
        command = ['pipenv', 'run', 'invenio', 'roles', 'create', 'admin']
        run_interactive(command)

        command = [
            'pipenv', 'run', 'invenio', 'access', 'allow',
            'superuser-access', 'role', 'admin'
        ]
        run_interactive(command)

        # Without the self.cli_config.get_services_setup() check
        # this throws an error on re-runs
        # TODO: invenio-indexer#115 should make it idempotent
        command = ['pipenv', 'run', 'invenio', 'index', 'init']
        run_interactive(command)

        self.cli_config.update_services_setup(True)

    def demo(self):
        """Add demo records into the instance."""
        command = ['pipenv', 'run', 'invenio', 'rdm-records', 'demo']
        run_interactive(command)

    def setup(self, force, demo_data=True):
        """Local start of containers (services).

        A check in invenio-cli's config file is done to see if one-time setup
        has been executed before.
        """
        self.ensure_containers_running()
        if force:
            self._cleanup()
        if not self.cli_config.get_services_setup():
            self._setup()
        if demo_data:
            self.demo()

        # FIXME: Implemente proper error control.
        # Use run_cmd and check output instead of run_interactive
        return ProcessResponse(
            output="Successfully setup all services.",
            status_code=0
        )
