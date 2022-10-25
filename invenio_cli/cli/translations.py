# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

from pathlib import Path

import click

from ..commands import TranslationsCommands
from .utils import pass_cli_config, run_steps


@click.group()
def translations():
    """Commands for translations management."""


@translations.command()
@click.option(
    "--babel-ini",
    "-b",
    default="translations/babel.ini",
    help="Relative path to babel.ini (including filename).",
)
@pass_cli_config
def extract(cli_config, babel_ini):
    """Extract messages for i18n support (translations)."""
    click.secho("Extracting messages...", fg="green")
    steps = TranslationsCommands.extract(
        msgid_bugs_address=cli_config.get_author_email(),
        copyright_holder=cli_config.get_author_name(),
        babel_file=cli_config.get_project_dir() / Path("translations/babel.ini"),
        output_file=cli_config.get_project_dir() / Path("translations/messages.pot"),
        input_dirs=cli_config.get_project_dir(),
    )
    on_fail = "Failed to extract messages."
    on_success = "Messages extracted successfully."

    run_steps(steps, on_fail, on_success)


@translations.command()
@click.option("--locale", "-l", required=True, help="Locale to initialize.")
@pass_cli_config
def init(cli_config, locale):
    """Initialized message catalog for a given locale."""
    click.secho("Initializing messages catalog...", fg="green")
    steps = TranslationsCommands.init(
        output_dir=cli_config.get_project_dir() / Path("translations/"),
        input_file=cli_config.get_project_dir() / Path("translations/messages.pot"),
        locale=locale,
    )
    on_fail = f"Failed to initialize message catalog for {locale}."
    on_success = f"Message catalog for {locale} initialized successfully."

    run_steps(steps, on_fail, on_success)


@translations.command()
@pass_cli_config
def update(cli_config):
    """Update messages catalog."""
    click.secho("Updating messages catalog...", fg="green")
    steps = TranslationsCommands.update(
        output_dir=cli_config.get_project_dir() / Path("translations/"),
        input_file=cli_config.get_project_dir() / Path("translations/messages.pot"),
    )
    on_fail = f"Failed to update message catalog."
    on_success = f"Message catalog updated successfully."

    run_steps(steps, on_fail, on_success)


@translations.command()
@click.option("--fuzzy", "-f", default=True, is_flag=True, help="Use fuzzyness.")
@pass_cli_config
def compile(cli_config, fuzzy):
    """Compile message catalog."""
    click.secho("Compiling catalog...", fg="green")
    commands = TranslationsCommands(
        project_path=cli_config.get_project_dir(),
        instance_path=cli_config.get_instance_path(),
    )
    steps = commands.compile(fuzzy=fuzzy)
    on_fail = "Failed to compile catalog."
    on_success = "Catalog compiled successfully."

    run_steps(steps, on_fail, on_success)
