# -*- coding: utf-8 -*-
#
# Copyright (C) 2026 CERN.
# Copyright (C) 2026 CESNET.
# Copyright (C) 2026 KTH Royal Institute of Technology.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Tests for translations commands."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from invenio_cli.cli.translations import translations
from invenio_cli.commands.translations import TranslationsCommands
from invenio_cli.helpers.cli_config import CLIConfig


@pytest.mark.parametrize(
    ("options", "use_fuzzy"),
    [([], False), (["--fuzzy"], True), (["-f"], True)],
)
def test_compile_cli_fuzzy_opt_in(mock_cli_config, tmp_path, options, use_fuzzy):
    """Exclude fuzzy translations unless the user explicitly opts in."""
    cli_config = Mock(spec=CLIConfig)
    cli_config.python_package_manager = mock_cli_config.python_package_manager
    cli_config.get_project_dir.return_value = tmp_path
    cli_config.get_instance_path.return_value = tmp_path / "instance"

    with patch("invenio_cli.cli.translations.run_steps") as run_steps:
        result = CliRunner().invoke(translations, ["compile", *options], obj=cli_config)

    assert result.exit_code == 0, result.output
    steps = run_steps.call_args.args[0]
    assert ("--use-fuzzy" in steps[0].cmd) is use_fuzzy
    assert f"--directory={tmp_path / 'translations'}" in steps[0].cmd


def test_compile_defaults_without_fuzzy(mock_cli_config, tmp_path):
    """Programmatic compilation excludes fuzzy translations by default."""
    commands = TranslationsCommands(mock_cli_config, project_path=tmp_path)

    steps = commands.compile(symlink=False)

    assert "--use-fuzzy" not in steps[0].cmd


def test_update_without_fuzzy_matching(mock_cli_config, tmp_path):
    """Catalog updates do not reuse translations from similar source strings."""
    commands = TranslationsCommands(mock_cli_config)

    steps = commands.update(output_dir=tmp_path, input_file=tmp_path / "messages.pot")

    assert steps[0].cmd == [
        "pipenv",
        "run",
        "pybabel",
        "update",
        "--no-fuzzy-matching",
        f"--output-dir={tmp_path}",
        f"--input-file={tmp_path / 'messages.pot'}",
    ]


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
