# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2021 CERN.
# Copyright (C) 2019 Northwestern University.
# Copyright (C) 2022 Forschungszentrum Jülich GmbH.
# Copyright (C) 2024-2025 Graz University of Technology.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import os
from pathlib import Path

import click

from ..commands import (
    Commands,
    ContainersCommands,
    LocalCommands,
    RequirementsCommands,
    ServicesCommands,
    UpgradeCommands,
)
from ..helpers.cli_config import CLIConfig
from ..helpers.cookiecutter_wrapper import CookiecutterWrapper
from .assets import assets
from .containers import containers
from .install import install
from .packages import packages
from .services import services
from .translations import translations
from .utils import (
    combine_decorators,
    handle_process_response,
    pass_cli_config,
    run_steps,
)


@click.group()
@click.version_option()
@click.pass_context
def invenio_cli(ctx):
    """Initialize CLI context."""


invenio_cli.add_command(assets)
invenio_cli.add_command(containers)
invenio_cli.add_command(install)
invenio_cli.add_command(packages)
invenio_cli.add_command(services)
invenio_cli.add_command(translations)


@invenio_cli.command("check-requirements")
@click.option(
    "--development",
    "-d",
    default=False,
    is_flag=True,
    help="Check requirements for a local development installation.",
)
def check_requirements(development):
    """Checks the system fulfills the pre-requirements."""
    click.secho("Checking pre-requirements...", fg="green")
    steps = RequirementsCommands.check(development)
    on_fail = "Pre requisites not met."
    on_success = "All requisites are fulfilled."

    run_steps(steps, on_fail, on_success)


@invenio_cli.command()
@pass_cli_config
def shell(cli_config):
    """Shell command."""
    Commands(cli_config).shell()


@invenio_cli.command()
@click.option(
    "--debug/--no-debug",
    "-d/",
    default=False,
    is_flag=True,
    help="Enable Flask development mode (default: disabled).",
)
@pass_cli_config
def pyshell(cli_config, debug):
    """Python shell command."""
    Commands(cli_config).pyshell(debug=debug)


@invenio_cli.command()
@click.argument(
    "flavour",
    type=click.Choice(["RDM", "ILS"], case_sensitive=False),
    default="RDM",
    required=False,
)
@click.option(
    "-t", "--template", required=False, help="Cookiecutter path or git url to template"
)
@click.option(
    "-c",
    "--checkout",
    required=False,
    help="Branch, tag or commit to checkout if --template is a git url",
)  # noqa
@click.option(
    "--user-input/--no-input",
    default=True,
    help="If input is disabled, uses the defaults (if --config is also passed, uses values from an .invenio config file).",  # noqa
)
@click.option(
    "--config", required=False, help="The .invenio configuration file to use."
)
def init(flavour, template, checkout, user_input, config):
    """Initializes the application according to the chosen flavour."""
    click.secho(
        "Initializing {flavour} application...".format(flavour=flavour), fg="green"
    )

    cookiecutter_kwargs = {
        "template": template,
        "checkout": checkout,
        "no_input": not user_input,
        "config": config,
    }
    cookiecutter_wrapper = CookiecutterWrapper(flavour, **cookiecutter_kwargs)

    try:
        click.secho("Running cookiecutter...", fg="green")
        project_dir = cookiecutter_wrapper.cookiecutter()

        click.secho("Writing invenio-cli config files...", fg="green")
        saved_replay = cookiecutter_wrapper.get_replay()
        CLIConfig.write(project_dir, flavour, saved_replay)

        click.secho("Creating logs directory...", fg="green")
        os.mkdir(Path(project_dir) / "logs")

    except Exception as e:
        click.secho(str(e), fg="red")

    finally:
        cookiecutter_wrapper.remove_config()


@invenio_cli.group("run", invoke_without_command=True)
@click.pass_context
def run_group(ctx):
    """Run command group."""
    # For backward compatibility
    if ctx.invoked_subcommand is None:
        ctx.invoke(run_all)


services_option = click.option(
    "--services/--no-services",
    "-s/-n",
    default=True,
    is_flag=True,
    help="Enable/disable dockerized services (default: enabled).",
)
web_options = combine_decorators(
    click.option(
        "--host",
        "-h",
        default=None,
        help="The interface to bind to. The default is defined in the CLIConfig.",
    ),
    click.option(
        "--port",
        "-p",
        default=None,
        help="The port to bind to. The default is defined in the CLIConfig.",
    ),
    click.option(
        "--debug/--no-debug",
        "-d/",
        default=True,
        is_flag=True,
        help="Enable/disable debug mode including auto-reloading (default: enabled).",
    ),
)


@run_group.command("web")
@services_option
@web_options
@pass_cli_config
def run_web(cli_config, host, port, debug, services):
    """Starts the local development web server."""
    if services:
        cmds = ServicesCommands(cli_config)
        response = cmds.ensure_containers_running()
        # fail and exit if containers are not running
        handle_process_response(response)

    host = host or cli_config.get_web_host()
    port = port or cli_config.get_web_port()

    commands = LocalCommands(cli_config)
    processes = commands.run_web(host=host, port=str(port), debug=debug)
    for proc in processes:
        proc.wait()


worker_options = combine_decorators(
    click.option(
        "--celery-log-file",
        default=None,
        help="Celery log file (default: None, this means logging to stderr)",
    ),
    click.option(
        "--celery-log-level",
        default="INFO",
        help="Celery log level (default: INFO)",
    ),
    click.option(
        "--jobs-scheduler/--no-jobs-scheduler",
        default=True,
        help="Enable/disable separate jobs scheduler (default: enabled)",
    ),
)


@run_group.command("worker")
@services_option
@worker_options
@pass_cli_config
def run_worker(cli_config, services, celery_log_file, celery_log_level, jobs_scheduler):
    """Starts the local development server."""
    if services:
        cmds = ServicesCommands(cli_config)
        response = cmds.ensure_containers_running()
        # fail and exit if containers are not running
        handle_process_response(response)

    commands = LocalCommands(cli_config)
    processes = commands.run_worker(
        celery_log_file=celery_log_file,
        celery_log_level=celery_log_level,
        jobs_scheduler=jobs_scheduler,
    )
    for proc in processes:
        proc.wait()


@run_group.command("all")
@services_option
@web_options
@worker_options
@pass_cli_config
def run_all(
    cli_config,
    host,
    port,
    debug,
    services,
    celery_log_file,
    celery_log_level,
    jobs_scheduler,
):
    """Starts web and worker development servers."""
    if services:
        cmds = ServicesCommands(cli_config)
        response = cmds.ensure_containers_running()
        # fail and exit if containers are not running
        handle_process_response(response)

    host = host or cli_config.get_web_host()
    port = port or cli_config.get_web_port()

    commands = LocalCommands(cli_config)
    processes = commands.run_all(
        host=host,
        port=str(port),
        debug=debug,
        services=services,
        celery_log_file=celery_log_file,
        celery_log_level=celery_log_level,
        jobs_scheduler=jobs_scheduler,
    )
    for proc in processes:
        proc.wait()


@invenio_cli.command()
@pass_cli_config
def destroy(cli_config):
    """Removes all associated resources (containers, images, volumes)."""
    commands = Commands(cli_config)
    services = ContainersCommands(cli_config)
    click.secho("Destroying containers, volumes, virtual environment...", fg="green")
    steps = commands.destroy()  # Destroy virtual environment
    steps.extend(services.destroy())  # Destroy services
    on_fail = (
        "Failed to destroy instance. You can destroy only services "
        + "using the services command: invenio-cli services destroy"
    )
    on_success = "Instance destroyed."

    run_steps(steps, on_fail, on_success)


@invenio_cli.command()
@click.option("--script", required=True, help="The path of custom migration script.")
@pass_cli_config
def upgrade(cli_config, script):
    """Upgrades the current instance to a newer version."""
    steps = UpgradeCommands(cli_config).upgrade(script)
    on_fail = "Upgrade failed."
    on_success = "Upgrade sucessfull."

    run_steps(steps, on_fail, on_success)
