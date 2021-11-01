# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import re
import sys
from os import listdir

from ..helpers.process import ProcessResponse, run_cmd, run_interactive
from .steps import FunctionStep


class RequirementsCommands(object):
    """Pre-requirements check."""

    @classmethod
    def _version_from_string(cls, string):
        """Gets the version from a given string."""
        groups = re.search(r'[0-9]*\.[0-9]*\.[0-9]*', string)
        return groups.group(0)

    @classmethod
    def _check_version(cls, binary, version,
                       major, minor=-1, patch=-1, exact=False):
        """Checks a version."""
        parts = version.split('.')

        if len(parts) != 3:
            return ProcessResponse(
                error=f"{binary} incorrect version format or not found. "
                      "Check that it is installed correctly",
                status_code=1
            )

        parts = [int(num) for num in parts]

        version_ok = False
        if exact:
            major_match = parts[0] == major
            minor_match = minor == -1 or parts[1] == minor
            patch_match = patch == -1 or parts[2] == patch
            version_ok = major_match and minor_match and patch_match
        else:
            major_higher = parts[0] > major
            major_ok = parts[0] >= major
            minor_higher = major_ok and parts[1] > minor
            minor_ok = major_ok and parts[1] >= minor
            patch_ok = minor_ok and parts[2] >= patch
            version_ok = major_higher or minor_higher or patch_ok

        if version_ok:
            return ProcessResponse(
                output=f"{binary} version OK. Got {version}.",
                status_code=0
            )

        expected_version = major
        if minor > -1:
            expected_version = f"{major}.{minor}"
            if patch > -1:
                expected_version = f"{major}.{minor}.{patch}"

        return ProcessResponse(
            error=f"{binary} wrong version."
                  f"Got {parts} expected {expected_version}",
            status_code=1
        )

    @classmethod
    def check_node_version(cls, major, minor=-1, patch=-1, exact=False):
        """Check the node version."""
        # Output comes in the form of 'v14.4.0\n'
        result = run_cmd(["node", "--version"])
        version = cls._version_from_string(result.output.strip())
        return cls._check_version("Node", version, major, minor, patch, exact)

    @classmethod
    def check_python_version(cls, major, minor=-1, patch=-1, exact=False):
        """Check the python version."""
        # check the version of the currently executed Python, as
        # 'invenio-cli' will create a virtualenv with the stated Python
        # version (via pipenv) anyway
        version_info = sys.version_info
        version = "{}.{}.{}".format(
            version_info.major,
            version_info.minor,
            version_info.micro,
        )

        return cls._check_version(
            "Python", version, major, minor, patch, exact)

    @classmethod
    def check_docker_version(cls, major, minor=-1, patch=-1, exact=False):
        """Check the docker version."""
        # Output comes in the form of
        # 'Docker version 19.03.13, build 4484c46d9d\n'
        try:
            result = run_cmd(["docker", "--version"])
            version = cls._version_from_string(result.output.strip())
            return cls._check_version(
                "Docker", version, major, minor, patch, exact)
        except Exception as err:
            return ProcessResponse(
                error=f"Docker not found. Got {err}.", status_code=1)

    @classmethod
    def check_docker_compose_version(cls, major, minor=-1, patch=-1,
                                     exact=False):
        """Check the docker compose version."""
        # Output comes in the form of
        # 'docker-compose version 1.27.4, build 4484c46d9d\n'
        try:
            result = run_cmd(["docker-compose", "--version"])
            version = cls._version_from_string(result.output.strip())
            return cls._check_version(
                "Docker Compose", version, major, minor, patch, exact
            )
        except Exception as err:
            return ProcessResponse(
                error=f"Docker Compose not found. Got {err}.", status_code=1
            )

    @classmethod
    def check_imagemagick_version(cls, major, minor=-1, patch=-1,
                                  exact=False):
        """Check the ImageMagick version."""
        # Output comes in the form of 'ImageMagick, version 7.0.11-13\n'
        try:
            result = run_cmd(["convert", "--version"])
            version = cls._version_from_string(result.output.strip())
            return cls._check_version(
                "ImageMagick", version, major, minor, patch, exact
            )
        except Exception as err:
            return ProcessResponse(
                error=f"ImageMagick not found. Got {err}.",
                status_code=1,
            )

    @classmethod
    def check_pipenv_installed(cls):
        """Check the pipenv version."""
        # Output comes in the form of 'pipenv, version 2020.11.15\n'
        result = run_cmd(["pipenv", "--version"])

        parts = result.output.strip().split(',')
        if parts[0] != 'pipenv':
            return ProcessResponse(
                error=f"Pipenv not found. Got {result.error}.",
                status_code=1
            )

        version = cls._version_from_string(parts[1])

        return ProcessResponse(
                output=f"Pipenv OK. Got version {version}.",
                status_code=0
            )

    @classmethod
    def check_dev(cls):
        """Steps to check the development pre-requisites."""
        steps = [
            FunctionStep(
                func=cls.check_node_version,
                args={"major": 14, "exact": True},
                message="Checking Node version..."
            )
        ]

        return steps

    @classmethod
    def check(cls, development=False):
        """Steps to check the pre-requisites."""
        steps = [
            FunctionStep(
                func=cls.check_python_version,
                args={"major": 3, "minor": 6},
                message="Checking Python version..."
            ),
            FunctionStep(
                func=cls.check_pipenv_installed,
                message="Checking Pipenv is installed..."
            ),
            FunctionStep(
                func=cls.check_docker_version,
                args={"major": 0, "minor": 0},
                message="Checking Docker version..."
            ),
            FunctionStep(
                func=cls.check_docker_compose_version,
                args={"major": 1, "minor": 17},
                message="Checking Docker Compose version..."
            ),
            FunctionStep(
                func=cls.check_imagemagick_version,
                args={"major": 0, "minor": 0},
                message="Checking ImageMagick version...",
                skippable=True,
            )
        ]

        if development:
            steps.extend(cls.check_dev())

        return steps
