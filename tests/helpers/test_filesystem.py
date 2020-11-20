# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module docker_helper tests."""
import tempfile
from pathlib import Path

from invenio_cli.helpers.filesystem import get_created_files


def test_get_created_files():
    tmp_dir = tempfile.TemporaryDirectory()
    tmp_dir_path = Path(tmp_dir.name)
    (tmp_dir_path / 'foo').touch()
    (tmp_dir_path / 'bar').mkdir()
    (tmp_dir_path / 'bar' / 'baz').touch()

    files_tree = get_created_files(tmp_dir.name)

    expected_files_tree = {
        'foo': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',  # noqa
        'bar': {
            'baz': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855'  # noqa
        }
    }
    assert files_tree == expected_files_tree
