# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from ..helpers.cli_config import CLIConfig
from .steps import CommandStep


class UpgradeCommands(object):
    """Local installation commands."""

    def __init__(self, cli_config: CLIConfig):
        """Constructor."""
        self.cli_config = cli_config

    def upgrade(self, script_path):
        """Steps to perform an upgrade of the invenio instance.

        First, and alembic upgrade is launched to allow alembic to migrate the
        database using SQLAlchemy.
        Then, the custom script is executed.
        Last, the search indices are destroyed, initialized and rebuilt.
        It is a class method since it does not require any configuration.
        """
        pkg_man = self.cli_config.python_package_manager
        alembic_cmd = pkg_man.run_command("invenio", "alembic", "upgrade")
        destroy_index_cmd = pkg_man.run_command(
            "invenio", "index", "destroy", "--yes-i-know"
        )
        init_index_cmd = pkg_man.run_command("invenio", "index", "init")
        rec_rebuild_index_cmd = pkg_man.run_command(
            "invenio", "rdm-records", "rebuild-index"
        )
        comm_rebuild_index_cmd = pkg_man.run_command(
            "invenio", "communities", "rebuild-index"
        )
        script_cmd = pkg_man.run_command("invenio", "shell", script_path)

        steps = [
            CommandStep(
                cmd=alembic_cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Performing an alembic upgrade...",
            ),
            CommandStep(
                cmd=script_cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Executing data upgrade script...",
            ),
            CommandStep(
                cmd=destroy_index_cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Destroying indexes...",
            ),
            CommandStep(
                cmd=init_index_cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Creating new indexes...",
            ),
            CommandStep(
                cmd=rec_rebuild_index_cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Rebuilding records and vocabularies indices...",
            ),
            CommandStep(
                cmd=comm_rebuild_index_cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Rebuilding communities indices...",
            ),
        ]

        return steps
