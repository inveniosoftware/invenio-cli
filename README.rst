..
    SPDX-FileCopyrightText: 2019-2020 CERN.
    SPDX-FileCopyrightText: 2019-2020 Northwestern University.
    SPDX-FileCopyrightText: 2025-2026 Graz University of Technology.
    SPDX-License-Identifier: MIT

=================
 Invenio-Cli
=================

.. image:: https://github.com/inveniosoftware/invenio-cli/workflows/CI/badge.svg
        :target: https://github.com/inveniosoftware/invenio-cli/actions?query=workflow%3ACI

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
    $ invenio-cli init rdm
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

Customizations
==============

It is possible to choose between two python package managers: `pipenv` and `uv`.
To customize the python package manager it is necessary to add the line
`python_package_manager = VALUE` to the `.invenio` file in the `[cli]` section.
`VALUE` is `uv` or `pipenv`.

It is possible to choose between two javascript package managers: `npm` and
`pnpm`. To customize the python package manager it is
necessary to add the line `javascript_package_manager = VALUE` to the `.invenio`
file in the `[cli]` section. `VALUE` is `npm` or `pnpm`.

It is possible to choose between two assets builders: `webpack` and `rspack`. To
use `rspack` add `WEBPACKEXT_PROJECT = "invenio_assets.webpack:rspack_project"`
to the `invenio.cfg` file.

It is possible to send `invenio` commands to a long running RPC server instead
of starting a new Python process for each command. To enable this add the line
`use_rpc = true` to the `[cli]` section of the `.invenio` file. The server
listens on a Unix domain socket at `<instance_path>/rpc.sock` and is started
automatically when needed; invenio-cli stops it again on exit.


Containerized 'Production' environment
--------------------------------------

.. code-block:: console

    # Initialize environment and cd into <created folder>
    $ invenio-cli init rdm
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
