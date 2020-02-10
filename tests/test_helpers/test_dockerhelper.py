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
    # Needed to fake call to docker-compose --version but not call
    # to docker-compose up
    def fake_normalize_name(self, project_shortname):
        return 'project_shortname'

    with patch.object(DockerHelper, '_normalize_name', fake_normalize_name):
        docker_helper = DockerHelper('project-shortname', local=True)

    docker_helper.start_containers()

    patched_subprocess.run.assert_called_with(
        [
            'docker-compose', '--file', 'docker-compose.yml', 'up', '--build',
            '-d'
        ],
        check=True
    )

    with patch.object(DockerHelper, '_normalize_name', fake_normalize_name):
        docker_helper = DockerHelper('project-shortname', local=False)

    docker_helper.start_containers()

    patched_subprocess.run.assert_called_with(
        [
            'docker-compose', '--file', 'docker-compose.full.yml', 'up',
            '--build', '-d'
        ],
        check=True
    )
