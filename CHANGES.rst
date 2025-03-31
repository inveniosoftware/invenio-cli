..
    Copyright (C) 2019-2024 CERN.
    Copyright (C) 2019-2021 Northwestern University.
    Copyright (C) 2025      TU Wien.

    Invenio-Cli is free software; you can redistribute it and/or modify
    it under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

Version <next>

- versions: fix accidental creation of a tuple from the version string

Version 1.7.0 (released 2025-03-28)

- build: allow use of either `npm` or `pnpm` as JS package manager (via `.invenio`)

Version 1.6.1 (released 2025-03-27)

- versions: consider `pyproject.toml` when checking `App-{RDM,ILS}` dependency versions

Version 1.6.0 (released 2025-02-28)

- packages: allow use of either `pipenv` or `uv` as python package manager
- flask: replace `FLASK_ENV` with `FLASK_DEBUG`
- celery: allow setting a log level
- config: make host & port for both web and search configurable via `.invenio.private`
- run: introduce more fine-granular "web" and "worker" sub-commands

Version 1.5.0 (released 2024-08-01)

- dependencies: update for invenio-app-rdm v12

Version 1.4.0 (released 2024-07-12)

- services: add support for InvneioILS setup

Version 1.3.1 (released 2024-06-05)

- config: fix missing "instance_path" usage

Version 1.3.0 (released 2024-05-24)

- deps: pin docker to >=7.1.0 due to bug on requests
- services: add instance path to env on setup

Version 1.2.0 (released 2023-10-02)

- reload on invenio.cfg changes

Version 1.1.0 (released 2023-07-24)

- add compatibility for docker compose v2
- consider command errors when using install command and fail

Version 1.0.21 (released 2023-05-18)

- deps: support docker < 7 for compatibility with urllib3 v2

Version 1.0.20 (released 2023-03-134)

- setup: add queues initialisation to steps

Version 1.0.19 (released 2023-03-10)

- global: remove fail message on warning (i.e. soft failures)

Version 1.0.18 (released 2023-02-07)

- containerize: fix translation commands instance path

Version 1.0.17 (released 2023-01-30)

- requirements: check node version depending on app-rdm version

Version 1.0.16 (released 2023-01-30)

- bump cookiecutter to v11.0

Version 1.0.15 (released 2023-01-13)

- Setup: fix empty translation folder failing

Version 1.0.14 (released 2023-01-09)

- Add app-rdm fixtures to setup

Version 1.0.13 (released 2022-11-14)

- Allow compilation command to fail in case of missing catalogs.

Version 1.0.12 (released 2022-10-28)

- Adds support for translations (i18n) management commands.

Version 1.0.11 (released 2022-10-24)

- Add support for InvenioILS

Version 1.0.8 (released 2022-10-13)

- Fix issue when checking for services to be up
  and running correctly.

Version 1.0.7 (released 2022-10-10)

- Fix compat issue with RDM versions < v10

Version 1.0.6 (released 2022-10-10)

- Bump default RDM version.

Version 1.0.5 (released 2022-05-31)

- Bump click version.
- Bump default RDM version.
- Improve error handling.
- Add check for npm version.
- Move ImageMagick check to --development.

Version 1.0.4 (released 2022-02-14)

- Fixes an issue with virtualenv 20.13.1+ brining in setuptools 60.x which is
  incompatible with Celery v5.2.3. Once Celery v5.2.4 has been released, this
  fix is no longer needed.

Version 1.0.3 (released 2022-02-04)

- Added ``--no-input`` and ``--config=`` options to ``init`` to support running
  with predefined config and without requiring user input.

Version 1.0.0 (released 2021-08-05)

- Initial public release.
