..
    Copyright (C) 2019-2020 CERN.
    Copyright (C) 2019-2020 Northwestern University.

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

Command-line tool to create and manage an InvenioRDM instance.

Installation
============

.. code-block:: console

    $ pip install invenio-cli

Usage
=====

Local Development environment
-----------------------------

.. code-block:: console

    # Initialize environment and cd into <created folder>
    $ invenio-cli init --flavour=RDM
    $ cd <created folder>

    # Install locally
    # install python dependencies (pre-release versions needed for now),
    # link/copy assets + statics, install js dependencies, build assets and
    # final statics
    $ invenio-cli install --pre

    # Start and setup services (database, Elasticsearch, Redis, queue)
    $ invenio-cli services

    # Optional: add demo data
    $ invenio-cli demo --local

    # Run the server
    $ invenio-cli run

    # Update assets or statics
    $ invenio-cli update


Containerized 'Production' environment
--------------------------------------

.. code-block:: console

    # Initialize environment and cd into <created folder>
    $ invenio-cli init --flavour=RDM
    $ cd <created folder>

    # Spin-up InvenioRDM
    $ invenio-cli containerize

    # Optional: add demo data
    $ invenio-cli demo --containers

    # After updating statics or code, if you do not need to re-install JS
    # dependencies which can take time
    $ invenio-cli containerize --no-install-js


More Help
---------

.. code-block:: console

    # Get more help
    $ invenio-cli --help

Further documentation is available on https://invenio-cli.readthedocs.io/
