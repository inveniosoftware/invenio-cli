# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module commands/requirements.py's tests."""

from invenio_cli.commands.requirements import RequirementsCommands


def test_check_requirements():
    # major
    ok_major_higher = RequirementsCommands._check_version(
        "random", "2.0.0", major=1
    )
    assert ok_major_higher.status_code == 0

    ok_major_equal = RequirementsCommands._check_version(
        "random", "2.0.0", major=2
    )
    assert ok_major_equal.status_code == 0

    ok_major_lower = RequirementsCommands._check_version(
        "random", "2.0.0", major=3
    )
    assert ok_major_lower.status_code == 1

    # minor
    ok_minor_higher = RequirementsCommands._check_version(
        "random", "2.10.0", major=2, minor=3
    )
    assert ok_minor_higher.status_code == 0

    ok_minor_equal = RequirementsCommands._check_version(
        "random", "2.10.0", major=2, minor=10
    )
    assert ok_minor_equal.status_code == 0

    ok_minor_lower = RequirementsCommands._check_version(
        "random", "2.10.0", major=3, minor=3
    )
    assert ok_minor_lower.status_code == 1

    # patch
    ok_patch_higher = RequirementsCommands._check_version(
        "random", "2.10.4", major=2, minor=10, patch=3
    )
    assert ok_patch_higher.status_code == 0

    ok_patch_equal = RequirementsCommands._check_version(
        "random", "2.10.4", major=2, minor=10, patch=4
    )
    assert ok_patch_equal.status_code == 0

    ok_patch_lower = RequirementsCommands._check_version(
        "random", "2.10.4", major=3, minor=3, patch=10
    )
    assert ok_patch_lower.status_code == 1

    # exact
    ok_exact = RequirementsCommands._check_version(
        "random", "2.10.4", major=2, minor=10, patch=4
    )
    assert ok_exact.status_code == 0

    ok_exact = RequirementsCommands._check_version(
        "random", "2.10.4", major=2, minor=10, patch=4, exact=True
    )
    assert ok_exact.status_code == 0

    ok_exact = RequirementsCommands._check_version(
        "random", "10.14.4", major=2, minor=10, patch=4, exact=True
    )
    assert ok_exact.status_code == 1
