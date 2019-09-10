# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# Invenio-Scripts is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module tests."""

from __future__ import absolute_import, print_function

from flask import Flask

from invenio_scripts import InvenioScripts


def test_version():
    """Test version import."""
    from invenio_scripts import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioScripts(app)
    assert 'invenio-scripts' in app.extensions

    app = Flask('testapp')
    ext = InvenioScripts()
    assert 'invenio-scripts' not in app.extensions
    ext.init_app(app)
    assert 'invenio-scripts' in app.extensions


def test_view(base_client):
    """Test view."""
    res = base_client.get("/")
    assert res.status_code == 200
    assert 'Welcome to Invenio-Scripts' in str(res.data)
