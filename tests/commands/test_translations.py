# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
# Copyright (C) 2026 CESNET.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for translations commands."""

from pathlib import Path

import pytest

from invenio_cli.commands.translations import TranslationsCommands


@pytest.fixture
def temp_pot_file(tmp_path):
    """Create a temporary .pot file with absolute paths."""
    pot_file = tmp_path / "messages.pot"
    pot_file.write_text(
        "# Translations template\n"
        "#, fuzzy\n"
        'msgid ""\n'
        'msgstr ""\n'
        f"#: {tmp_path}/test.py:1\n"
        'msgid "test message"\n'
        'msgstr ""\n'
    )
    return pot_file


def test_normalize_paths(temp_pot_file, tmp_path):
    """Test that absolute paths are normalized to relative paths."""
    commands = TranslationsCommands(cli_config=None, project_path=tmp_path)

    commands._normalize_paths(str(temp_pot_file), tmp_path)
    content = temp_pot_file.read_text()

    assert str(tmp_path) not in content
    assert "test.py:1" in content
    assert "#: test.py:1" in content


def test_normalize_paths_no_project_path(temp_pot_file, tmp_path):
    """Test that normalization works when project_path is None."""
    commands = TranslationsCommands(cli_config=None, project_path=None)
    original_content = temp_pot_file.read_text()
    commands._normalize_paths(str(temp_pot_file), None)

    normalized_content = temp_pot_file.read_text()
    assert original_content == normalized_content


def test_normalize_paths_file_not_exists(tmp_path):
    """Test that normalization handles non-existent files gracefully."""
    commands = TranslationsCommands(cli_config=None, project_path=tmp_path)

    # Run the normalization on a non-existent file - should not crash
    commands._normalize_paths(str(tmp_path / "nonexistent.pot"), tmp_path)
