..
    Copyright (C) 2019-2020 CERN.
    Copyright (C) 2019-2020 Northwestern University.
    Copyright (C) 2025 Graz University of Technology.

    Invenio-Cli is free software; you can redistribute it and/or modify
    it under the terms of the MIT License; see LICENSE file for more details.

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
`pipenv` is the default one. To customize the python package manager it is
necessary to add the line `python_package_manager = VALUE` to the `.invenio`
file. `VALUE` is `uv` or `pipenv`.

It is possible to choose between two javascript package managers: `npm` and
`pnpm`. `npm` is the default one. To customize the python package manager it is
necessary to add the line `javascript_package_manager = VALUE` to the `.invenio`
file. `VALUE` is `npm` or `pnpm`.

It is possible to choose between two assets builders: `webpack` and `rspack`.
`webpack` is the default one. To use `rspack` add `WEBPACKEXT_PROJECT =
"invenio_assets.webpack:rspack_project"` to the `invenio.cfg` file.

It is possible to use a long running invenio rpc-server by starting it with
`invenio rpc-server start --port 5001`. This should only be done if you know the
drawbacks. The server has to be restarted if code which the server uses has been
updated. Further it is not necessary to use a long running invenio rpc-server
since it will be started on every invenio-cli command a new rpc-server
nevertheless if no rpc-server runs already.

The javascript package manager uses a lock file like the python package manager.
This file `pnpm-lock.yaml` for `pnpm` and `packages-lock.json` for `npm` will be
symlinked to the `var/instance/assets/` directory.

Hints
=====

`uv`

The development with `uv` is a little bit different than with `pipenv`. If there
is a `uv.lock` file packages have to be updated manually or by removing the
`uv.lock` file. The absence of the `uv.lock` file triggeres a new dependency
resolving call which takes into account of new released packages. It would also
be possible to use the `uv sync --upgrade` feature of `uv` but this installs
also beta versions of packages which is not recommended. It may sound strange to
remove the `uv.lock` file, but `uv` is that fast that deleting the `.venv`
directory and the `uv.lock` file is the easiest and fastest and safest way to
upgrade the packages.

`rcp-server`

To use `pnpm` with the `rpc-server` it is necessary to add
`WEBPACKEXT_NPM_PKG_CLS = "pynpm:PNPMPackage"` to the `invenio.cfg` file.


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
