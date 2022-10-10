..
    Copyright (C) 2019-2021 CERN.
    Copyright (C) 2019-2021 Northwestern University.

    Invenio-Cli is free software; you can redistribute it and/or modify
    it under the terms of the MIT License; see LICENSE file for more details.

Changes
=======

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
