# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import click

from ..helpers.cli_config import CLIConfig
from ..helpers.process import run_cmd

pass_cli_config = click.make_pass_decorator(CLIConfig, ensure=True)


def run_steps(steps, fail_message, success_message):
    """Run a series of steps."""
    for test in steps:
        click.secho(message=test.message, fg="green")
        result = test.execute()
        if result.status_code > 0:
            if result.error:
                fail_message = fail_message + f"\nErrors: {result.error}"
            if result.output:
                fail_message = fail_message + f"\nOutput: {result.output}"

            click.secho(fail_message, fg="red")
            exit(1)
        elif result.output:
            click.secho(message=result.output, fg="green")
    else:
        click.secho(message=success_message, fg="green")


def calculate_instance_path():
    """Caclulates instance path based on current venv."""
    result = run_cmd(
            ['pipenv', 'run', 'invenio', 'shell', '--no-term-title',
                '-c', '"print(app.instance_path, end=\'\')"']
        )
    return result.output.strip()
