# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Module docker_helper tests."""
from unittest.mock import patch

from invenio_cli.helpers.docker_helper import DockerHelper


@patch('invenio_cli.helpers.docker_helper.subprocess')
def test_start_containers(patched_subprocess):
    docker_helper = DockerHelper(local=True)

    docker_helper.start_containers()

    patched_subprocess.run.assert_called_with(
        [
            'docker-compose', '--file', 'docker-compose.yml', 'up', '--build',
            '--detach'
        ]
    )

    docker_helper = DockerHelper(local=False)

    docker_helper.start_containers()

    patched_subprocess.run.assert_called_with(
        [
            'docker-compose', '--file', 'docker-compose.full.yml', 'up',
            '--build', '--detach'
        ]
    )
