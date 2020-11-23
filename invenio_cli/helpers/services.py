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

import click

from .process import run_cmd


def es_healthcheck(*args, **kwargs):
    """Elasticsearch healthcheck."""
    verbose = kwargs['verbose']

    return run_cmd([
        "curl", "-f",
        "localhost:9200/_cluster/health?wait_for_status=yellow"
    ])


def postgresql_healthcheck(*args, **kwargs):
    """Postgresql healthcheck."""
    filepath = kwargs['filepath']
    verbose = kwargs['verbose']

    return run_cmd([
        "docker-compose", "--file", filepath,
        "exec", "-T", "db", "bash", "-c", "pg_isready",
    ])


def mysql_healthcheck(*args, **kwargs):
    """Mysql healthcheck."""
    filepath = kwargs['filepath']
    verbose = kwargs['verbose']
    password = kwargs['project_shortname']

    return run_cmd([
        "docker-compose", "--file", filepath,
        "exec", "-T", "db", "bash", "-c",
        f"mysql -p{password} -e \"select Version();\"",
    ])


def redis_healthcheck(*args, **kwargs):
    """Redis healthcheck."""
    filepath = kwargs['filepath']
    verbose = kwargs['verbose']

    return run_cmd([
        "docker-compose", "--file", filepath,
        "exec", "-T", "cache", "bash", "-c",
        "redis-cli ping", "|", "grep 'PONG'", "&>/dev/null;",
    ])


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
            ).status_code == 0

        if not ready:
            click.secho(f"Unable to boot up {service}", fg="red")
            exit(1)
        else:
            click.secho(f"{service} up and running!", fg="green")
