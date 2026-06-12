# SPDX-FileCopyrightText: 2026 CERN.
# SPDX-License-Identifier: MIT

"""Version helper tests."""

from invenio_cli.helpers.cli_config import CLIConfig
from invenio_cli.helpers.versions import rdm_version


def test_rdm_version_without_cli_config_reads_dependency_files(tmp_path, monkeypatch):
    """Callers without a project context (check-requirements) stay valid."""
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "site"\ndependencies = ["invenio-app-rdm~=13.0.0"]\n'
    )
    monkeypatch.chdir(tmp_path)
    assert rdm_version() == [13, 0, 0]


def test_rdm_version_prefers_the_pinned_version(tmp_path, monkeypatch):
    """An app_rdm pin in the private config wins over dependency files."""
    (tmp_path / ".invenio").write_text("[cli]\n")
    (tmp_path / ".invenio.private").write_text("[cli]\napp_rdm = 14.1.0\n")
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "site"\ndependencies = ["invenio-app-rdm~=13.0.0"]\n'
    )
    monkeypatch.chdir(tmp_path)
    assert rdm_version(CLIConfig(tmp_path)) == [14, 1, 0]
