..
    Copyright (C) 2019 CERN.
    Copyright (C) 2019 Northwestern University.

    Invenio-Cli is free software; you can redistribute it and/or modify
    it under the terms of the MIT License; see LICENSE file for more details.

=================
 Invenio-Cli
=================

.. image:: https://img.shields.io/travis/inveniosoftware/invenio-cli.svg
        :target: https://travis-ci.org/inveniosoftware/invenio-cli

.. image:: https://img.shields.io/coveralls/inveniosoftware/invenio-cli.svg
        :target: https://coveralls.io/r/inveniosoftware/invenio-cli

.. image:: https://img.shields.io/github/tag/inveniosoftware/invenio-cli.svg
        :target: https://github.com/inveniosoftware/invenio-cli/releases

.. image:: https://img.shields.io/pypi/dm/invenio-cli.svg
        :target: https://pypi.python.org/pypi/invenio-cli

.. image:: https://img.shields.io/github/license/inveniosoftware/invenio-cli.svg
        :target: https://github.com/inveniosoftware/invenio-cli/blob/master/LICENSE

Invenio module that allows the creation of applications building workflows

Installation
============

.. code-block:: console

    (<custom virtualenv>)$ pip install invenio-cli

Usage
=====


Local Development environment
-----------------------------

.. code-block:: console

    # Initialize environment and cd into <created folder>
    (<custom virtualenv>)$ invenio-cli init --flavour=RDM --verbose
    (<custom virtualenv>)$ cd <created folder>

    # Build Docker image and assets: very important to have dependencies
    # installed by this command appear in your <custom virtualenv>
    (<custom virtualenv>)$ invenio-cli build --local --pre --verbose

    # Setup services (database, Elasticsearch, Redis, queue)
    (<custom virtualenv>)$ invenio-cli setup --local --verbose

    # Optional: add demo data
    (<custom virtualenv>)$ invenio-cli demo --local --verbose

    # Run the server
    (<custom virtualenv>)$ invenio-cli server --local --verbose

    # Destroy the instances
    (<custom virtualenv>)$ invenio-cli destroy --local --verbose

    # Get more help
    (<custom virtualenv>)$ invenio-cli --help


Containerized 'Production' environment
--------------------------------------

Just like the above, except with ``--containers``:

.. code-block:: console

    # Initialize environment and cd into <created folder>
    (<custom virtualenv>)$ invenio-cli init --flavour=RDM
    (<custom virtualenv>)$ cd <created folder>

    # Build Docker images
    (<custom virtualenv>)$ invenio-cli build --containers --pre --verbose

    # Setup services (database, Elasticsearch, Redis, queue)
    (<custom virtualenv>)$ invenio-cli setup --containers --verbose

    ...

Further documentation is available on https://invenio-cli.readthedocs.io/
