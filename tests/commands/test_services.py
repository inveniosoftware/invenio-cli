# SPDX-FileCopyrightText: 2026 California Institute of Technology.
# SPDX-License-Identifier: MIT

"""Services commands tests."""

from unittest.mock import Mock, patch

from invenio_cli.commands.services import ServicesCommands


@patch("invenio_cli.commands.services.ils_version", return_value=None)
@patch("invenio_cli.commands.services.rdm_version", return_value=None)
def _setup_messages(cli_config, *mocks):
    commands = ServicesCommands(cli_config, docker_helper=Mock())
    return [step.message for step in commands._setup()]


def test_setup_local_storage_skips_bucket_creation(mock_cli_config):
    assert "Creating default S3 bucket..." not in _setup_messages(mock_cli_config)


def test_setup_s3_storage_creates_bucket_before_location(mock_cli_config):
    mock_cli_config.get_file_storage = lambda: "S3"
    messages = _setup_messages(mock_cli_config)

    bucket_index = messages.index("Creating default S3 bucket...")
    assert messages[bucket_index + 1] == "Creating files location..."


def test_s3_create_default_bucket(mock_cli_config):
    commands = ServicesCommands(mock_cli_config, docker_helper=Mock())
    (step,) = commands.s3_create_default_bucket()

    assert step.cmd == ["pipenv", "run", "invenio", "s3", "create-bucket", "default"]
    assert step.skippable
