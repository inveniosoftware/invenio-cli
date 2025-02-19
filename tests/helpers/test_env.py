# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2025 Graz University of Technology.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test environment variables context manager."""

import os

from invenio_cli.helpers.env import env


def test_env():
    """Test environment variables context manager."""
    assert "SERVER_NAME" not in os.environ
    assert "FLASK_DEBUG" not in os.environ

    os.environ["FLASK_DEBUG"] = "true"
    with env(SERVER_NAME="example.com", FLASK_DEBUG="false"):
        assert os.environ["SERVER_NAME"] == "example.com"
        assert os.environ["FLASK_DEBUG"] == "false"

    assert os.environ["FLASK_DEBUG"] == "true"
    assert "SERVER_NAME" not in os.environ
