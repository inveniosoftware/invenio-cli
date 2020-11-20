# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio CLI Service class."""

#####
# IMPORTANT NOTE: If you are going to modify any code here.
# Check `docker-service-cli` since the original code belongs there,
# and any bug might have already been fixed there.
# The reason for the copy-paste was to simplify the complexity of the
# integration. Might be integrated in the future when `docker-services-cli`
# reaches a higher maturity level.
#####

import time
from os import path
from subprocess import PIPE, Popen, check_call

import click


def _run_healthcheck_command(command, verbose=False):
    """Runs a given command, returns True if it succeeds, False otherwise."""
    p = Popen(command, stdout=PIPE, stderr=PIPE)
    output, error = p.communicate()
    output = output.decode("utf-8")
    error = error.decode("utf-8")
    if p.returncode == 0:
        if verbose:
            click.secho(output, fg="green")
        return True
    if p.returncode != 0:
        if verbose:
            click.secho(
                f"Healthcheck failed.\nOutput: {output}\nError:{error}",
                fg="red"
            )
        return False


def es_healthcheck(*args, **kwargs):
    """Elasticsearch healthcheck."""
    verbose = kwargs['verbose']

    return _run_healthcheck_command([
        "curl",
        "-f",
        "localhost:9200/_cluster/health?wait_for_status=yellow"
    ], verbose)


def postgresql_healthcheck(*args, **kwargs):
    """Postgresql healthcheck."""
    filepath = kwargs['filepath']
    verbose = kwargs['verbose']

    return _run_healthcheck_command([
        "docker-compose",
        "--file",
        filepath,
        "exec",
        "-T",
        "db",
        "bash",
        "-c",
        "pg_isready",
    ], verbose)


def mysql_healthcheck(*args, **kwargs):
    """Mysql healthcheck."""
    filepath = kwargs['filepath']
    verbose = kwargs['verbose']
    password = kwargs['project_shortname']

    return _run_healthcheck_command([
        "docker-compose",
        "--file",
        filepath,
        "exec",
        "-T",
        "db",
        "bash",
        "-c",
        f"mysql -p{password} -e \"select Version();\"",
    ], verbose)


def redis_healthcheck(*args, **kwargs):
    """Redis healthcheck."""
    filepath = kwargs['filepath']
    verbose = kwargs['verbose']

    return _run_healthcheck_command([
        "docker-compose",
        "--file",
        filepath,
        "exec",
        "-T",
        "cache",
        "bash",
        "-c",
        "redis-cli ping",
        "|",
        "grep 'PONG'",
        "&>/dev/null;",
    ], verbose)


HEALTHCHECKS = {
    "es": es_healthcheck,
    "postgresql": postgresql_healthcheck,
    "mysql": mysql_healthcheck,
    "redis": redis_healthcheck,
    "sqlite": (lambda *args, **kwargs: True)
}
"""Health check functions module path, as string."""


def wait_for_services(
    services,
    project_shortname,
    filepath="docker-services.yml",
    max_retries=6,
    verbose=False,
):
    """Wait for services to be up.

    It performs configured healthchecks in a serial fashion, following the
    order given in the ``up`` command. If the services is an empty list, to be
    compliant with `docker-compose` it will perform the healthchecks of all the
    services.
    """
    if len(services) == 0:
        services = HEALTHCHECKS.keys()

    for service in services:
        exp_backoff_time = 2
        try_ = 1
        # Using plain __import__ to avoid depending on invenio-base
        check = HEALTHCHECKS[service]
        ready = check(
            filepath=filepath,
            verbose=verbose,
            project_shortname=project_shortname,
        )
        while not ready and try_ < max_retries:
            click.secho(
                f"{service} not ready at {try_} retries, waiting " +
                f"{exp_backoff_time}s",
                fg="yellow"
            )
            try_ += 1
            time.sleep(exp_backoff_time)
            exp_backoff_time *= 2
            ready = check(
                filepath=filepath,
                verbose=verbose,
                project_shortname=project_shortname,
            )

        if not ready:
            click.secho(f"Unable to boot up {service}", fg="red")
            exit(1)
        else:
            click.secho(f"{service} up and running!", fg="green")
