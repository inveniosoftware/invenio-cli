# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import click

from ..helpers.cli_config import CLIConfig

pass_cli_config = click.make_pass_decorator(CLIConfig, ensure=True)


def run_steps(steps, fail_message, success_message):
    """Run a series of steps."""
    for step in steps:
        click.secho(message=step.message, fg="green")
        response = step.execute()
        handle_process_response(response, fail_message=fail_message)
    else:
        click.secho(message=success_message, fg="green")


def handle_process_response(response, fail_message=None):
    """Handle the `ProcessResponse` obj after cmd execution."""
    msg = ""
    is_error = response.status_code > 0
    if is_error:
        if response.error:
            msg = f"Errors: {response.error}"
        if response.output:
            msg = f"Output: {response.output}"

        if fail_message:
            msg = fail_message + "\n" + msg

        click.secho(msg, fg="red")
        exit(1)
    elif response.warning:
        if response.error:
            msg = f"Errors: {response.error}"
        if response.output:
            msg = f"Output: {response.output}"

        if fail_message:
            msg = fail_message + "\n" + msg

        click.secho(msg, fg="yellow")
    elif response.output:
        click.secho(message=response.output, fg="green")
