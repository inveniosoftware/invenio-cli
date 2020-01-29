# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2019 CERN.
# Copyright (C) 2019 Northwestern University.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Filesystem helper functions."""

import errno
import hashlib
import os
from os.path import isdir
from pathlib import Path

# Defining buffer size to avoid using too much memory
BUF_SIZE = 65536  # 64 KB


def hash_file(path_to_file):
    """Hash file to check for consistency."""
    sha256 = hashlib.sha256()

    with open(path_to_file, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            sha256.update(data)

    return sha256.hexdigest()


def get_created_files(folder):
    """Return the generated tree of files (and their hash) and folders."""
    files = {}
    for name in os.listdir(folder):
        path = Path(folder)  # Current path

        # Add files and their hash
        if not isdir(path / name):
            files[name] = hash_file(path / name)
        # Add dirs and their files
        else:
            files[name] = get_created_files(path / name)

    return files


def force_symlink(target, link_name):
    """Forcefully create symlink at link_name pointing to target."""
    try:
        os.symlink(target, link_name)
    except OSError as e:
        if e.errno == errno.EEXIST:
            os.remove(link_name)
            os.symlink(target, link_name)
