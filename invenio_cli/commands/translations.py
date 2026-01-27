# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from ..commands import Commands
from ..helpers.cli_config import CLIConfig
from ..helpers.filesystem import force_symlink
from .steps import CommandStep, FunctionStep


class TranslationsCommands(Commands):
    """Translations CLI commands."""

    def __init__(self, cli_config: CLIConfig, project_path=None, instance_path=None):
        """Constructor."""
        self.cli_config = cli_config
        self.project_path = project_path
        self.instance_path = instance_path

    def extract(
        self,
        babel_file,
        output_file,
        input_dirs,
        msgid_bugs_address,
        copyright_holder,
        add_comments="NOTE",
    ):
        """Extract messages from source code and templates."""
        pkg_man = self.cli_config.python_package_manager
        cmd = pkg_man.run_command(
            "pybabel",
            "extract",
            f"--mapping-file={babel_file}",
            f"--output-file={output_file}",
            f"--input-dirs={input_dirs}",
            f"--msgid-bugs-address={msgid_bugs_address}",
            f"--copyright-holder={copyright_holder}",
            f"--add-comments={add_comments}",
        )

        return [
            CommandStep(
                cmd=cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message=f"Extracting i18n messages from {input_dirs}...",
            )
        ]

    def init(self, output_dir, input_file, locale):
        """Initialize a new language catalog."""
        pkg_man = self.cli_config.python_package_manager
        cmd = pkg_man.run_command(
            "pybabel",
            "init",
            f"--output-dir={output_dir}",
            f"--input-file={input_file}",
            f"--locale={locale}",
        )

        return [
            CommandStep(
                cmd=cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message=f"Initializing message catalog for {locale}...",
            )
        ]

    def update(self, output_dir, input_file):
        """Update the message catalog."""
        pkg_man = self.cli_config.python_package_manager
        cmd = pkg_man.run_command(
            "pybabel",
            "update",
            f"--output-dir={output_dir}",
            f"--input-file={input_file}",
        )

        return [
            CommandStep(
                cmd=cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Updating message catalog...",
            )
        ]

    def compile(
        self,
        directory=None,
        fuzzy=False,
        translation_folder="translations",
        symlink=True,
    ):
        """Compile the message catalog."""
        directory = directory or self.project_path / translation_folder
        pkg_man = self.cli_config.python_package_manager

        cmd = pkg_man.run_command(
            "pybabel",
            "compile",
            f"--directory={directory}",
        )

        if fuzzy:
            cmd.append("--use-fuzzy")

        steps = [
            CommandStep(
                cmd=cmd,
                env={"PIPENV_VERBOSITY": "-1"},
                message="Compiling message catalog...",
                skippable=True,
            ),
        ]

        if symlink:
            target_path = self.project_path / translation_folder
            link_path = self.instance_path / translation_folder

            steps.append(
                FunctionStep(
                    func=force_symlink,
                    args={
                        "target": target_path,
                        "link_name": link_path,
                    },
                    message="Symlinking translations...",
                )
            )

        return steps
