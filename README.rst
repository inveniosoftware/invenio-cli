..
    Copyright (C) 2019 CERN.

    Invenio-Scripts is free software; you can redistribute it and/or modify
    it under the terms of the MIT License; see LICENSE file for more details.

=================
 Invenio-Scripts
=================

.. image:: https://img.shields.io/travis/inveniosoftware/invenio-scripts.svg
        :target: https://travis-ci.org/inveniosoftware/invenio-scripts

.. image:: https://img.shields.io/coveralls/inveniosoftware/invenio-scripts.svg
        :target: https://coveralls.io/r/inveniosoftware/invenio-scripts

.. image:: https://img.shields.io/github/tag/inveniosoftware/invenio-scripts.svg
        :target: https://github.com/inveniosoftware/invenio-scripts/releases

.. image:: https://img.shields.io/pypi/dm/invenio-scripts.svg
        :target: https://pypi.python.org/pypi/invenio-scripts

.. image:: https://img.shields.io/github/license/inveniosoftware/invenio-scripts.svg
        :target: https://github.com/inveniosoftware/invenio-scripts/blob/master/LICENSE

Invenio module that allows the creation of applications building workflows

Example execution

.Development environment

```
$ inveniobuilder --flavor RDM --project-name my-site init
$ inveniobuilder --flavor RDM --project-name my-site build --base --app --dev
$ inveniobuilder --flavor RDM --project-name my-site server --dev --bg [--stop]
$ inveniobuilder --flavor RDM --project-name my-site setup --dev
$ # USE AWAY! :)
$ inveniobuilder --flavor RDM --project-name my-site destroy --dev
```

.Production environment

```
$ inveniobuilder --flavor RDM --project-name my-site init
$ inveniobuilder --flavor RDM --project-name my-site build --base --app
$ inveniobuilder --flavor RDM --project-name my-site server --bg [--stop]
$ inveniobuilder --flavor RDM --project-name my-site setup
$ # USE AWAY! :)
$ inveniobuilder --flavor RDM --project-name my-site destroy
```

Further documentation is available on
https://invenio-scripts.readthedocs.io/
