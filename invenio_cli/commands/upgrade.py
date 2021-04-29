# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from .steps import CommandStep


class UpgradeCommands(object):
    """Local installation commands."""

    @staticmethod
    def upgrade():
        """Steps to perform an upgrade of the invenio instance.

        First, and alembic upgrade is launched to allow alembic to migrate the
        database using SQLAlchemy.
        Then, the Elasticsearch indexes are destroyed, initialized and rebuilt.
        It is a class method since it does not require any configuration.
        """
        prefix = ['pipenv', 'run', 'invenio']
        alembic_cmd = prefix + ['alembic', 'upgrade']
        destroy_index_cmd = prefix + ['index', 'destroy', '--yes-i-know']
        init_index_cmd = prefix + ['index', 'init']
        rebuild_index_cmd = prefix + ['rdm-records', 'rebuild-index']

        steps = [
            CommandStep(
                cmd=alembic_cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message="Performing an alembic upgrade..."
            ),
            CommandStep(
                cmd=destroy_index_cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message="Destroying indexes..."
            ),
            CommandStep(
                cmd=init_index_cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message="Creating new indexes..."
            ),
            CommandStep(
                cmd=rebuild_index_cmd,
                env={'PIPENV_VERBOSITY': "-1"},
                message="Rebuilding indexes..."
            )
        ]

        return steps
