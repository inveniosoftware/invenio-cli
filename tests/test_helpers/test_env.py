# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test environment variables context manager."""

import os

from invenio_cli.helpers.env import env


def test_env():
    """Test environment variables context manager."""
    assert 'FLASK_ENV' not in os.environ
    assert 'FLASK_DEBUG' not in os.environ

    os.environ['FLASK_DEBUG'] = 'true'
    with env(FLASK_ENV='production', FLASK_DEBUG='false'):
        assert os.environ['FLASK_ENV'] == 'production'
        assert os.environ['FLASK_DEBUG'] == 'false'

    assert os.environ['FLASK_DEBUG'] == 'true'
    assert 'FLASK_ENV' not in os.environ
