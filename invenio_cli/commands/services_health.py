# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

#####
# IMPORTANT NOTE: If you are going to modify any code here.
# Check `docker-service-cli` since the original code belongs there,
# and any bug might have already been fixed there.
# The reason for the copy-paste was to simplify the complexity of the
# integration. Might be integrated in the future when `docker-services-cli`
# reaches a higher maturity level.
#####

import time

from ..helpers.process import run_cmd


class ServicesHealthCommands(object):
    """Services status commands."""

    @classmethod
    def search_healthcheck(cls, *args, **kwargs):
        """Open/Elasticsearch healthcheck."""
        verbose = kwargs["verbose"]

        return run_cmd(
            ["curl", "-f", "localhost:9200/_cluster/health?wait_for_status=yellow"]
        )

    @classmethod
    def postgresql_healthcheck(cls, *args, **kwargs):
        """Postgresql healthcheck."""
        filepath = kwargs["filepath"]
        verbose = kwargs["verbose"]

        return run_cmd(
            [
                "docker-compose",
                "--file",
                filepath,
                "exec",
                "-T",
                "db",
                "bash",
                "-c",
                "pg_isready",
            ]
        )

    @classmethod
    def mysql_healthcheck(cls, *args, **kwargs):
        """Mysql healthcheck."""
        filepath = kwargs["filepath"]
        verbose = kwargs["verbose"]
        password = kwargs["project_shortname"]

        return run_cmd(
            [
                "docker-compose",
                "--file",
                filepath,
                "exec",
                "-T",
                "db",
                "bash",
                "-c",
                f'mysql -p{password} -e "select Version();"',
            ]
        )

    @classmethod
    def redis_healthcheck(cls, *args, **kwargs):
        """Redis healthcheck."""
        filepath = kwargs["filepath"]
        verbose = kwargs["verbose"]

        return run_cmd(
            [
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
            ]
        )

    @classmethod
    def wait_for_service(
        cls,
        service,
        project_shortname,
        print_func,
        filepath="docker-services.yml",
        max_retries=6,
        verbose=False,
    ):
        """Wait for the given service to be up."""
        if service not in HEALTHCHECKS:
            raise RuntimeError(
                f"{service} not recognized. Available services: {HEALTHCHECKS.keys()}"
            )

        exp_backoff_time = 2
        try_ = 0
        check = HEALTHCHECKS[service]
        check_func = check["func"]
        initial_delay = check.get("initial_delay", 0)
        wait_initial_delay = initial_delay > 0
        ready = False

        while not ready and try_ < max_retries:
            response = check_func(
                filepath=filepath,
                verbose=verbose,
                project_shortname=project_shortname,
            )
            ready = response.status_code == 0

            if not ready:
                is_first_check = try_ == 0

                # some services might be particularly slow to start up
                if is_first_check and wait_initial_delay:
                    print_func(
                        f"{service} starting up, checking in {initial_delay}s...",
                    )
                    time.sleep(initial_delay)
                else:
                    print_func(
                        f"{service} not ready at {try_+1} retries, waiting "
                        + f"{exp_backoff_time}s...",
                    )
                    time.sleep(exp_backoff_time)
                    exp_backoff_time *= 2

                try_ += 1

        return ready


HEALTHCHECKS = {
    "search": {
        "func": ServicesHealthCommands.search_healthcheck,
        "initial_delay": 15,  # search cluster can be particularly slow to start
    },
    "postgresql": {
        "func": ServicesHealthCommands.postgresql_healthcheck,
        "initial_delay": 0,
    },
    "mysql": {
        "func": ServicesHealthCommands.mysql_healthcheck,
        "initial_delay": 0,
    },
    "redis": {
        "func": ServicesHealthCommands.redis_healthcheck,
        "initial_delay": 0,
    },
}
"""Health check functions module path, as string."""
