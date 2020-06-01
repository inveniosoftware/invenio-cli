# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Pytest fixtures."""

from os.path import exists

import pytest
from click.testing import CliRunner

from invenio_cli.cli import cli


@pytest.fixture()
def runner():
    """Click CLI runner."""
    runner = CliRunner()
    with runner.isolated_filesystem():
        yield runner


def test_init(runner):
    """Test init command."""
    result = runner.invoke(cli, ['init'])
    assert result.exit_code == 0
    assert exists('my-site')
    assert exists('my-site/.invenio')


def test_init_with_arg(runner):
    """Test init command."""
    result = runner.invoke(cli, ['init', 'rdm'])
    assert result.exit_code == 0
    assert exists('my-site')
    assert exists('my-site/.invenio')
