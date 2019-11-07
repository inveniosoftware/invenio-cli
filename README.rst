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

Usage
=====

Development environment
-----------------------

.. code-block:: console

    # Initialize environment
    $ invenio-cli --flavour=RDM init

    # Build Docker images
    $ invenio-cli build --dev --pre --lock

    # Run server and services
    $ invenio-cli run --dev --bg

    # Setup databases and Elasticsearch
    $ invenio-cli setup --dev

    # Destroy the instances
    $ invenio-cli destroy --dev

    # Get more help
    $ invenio-cli --help

Production environment
----------------------

Just like the above, except with ``--prod``:

.. code-block:: console

    # Initialize environment
    $ invenio-cli --flavour=RDM init

    # Build Docker images
    $ invenio-cli build --prod --lock

    ...

Further documentation is available on https://invenio-cli.readthedocs.io/
