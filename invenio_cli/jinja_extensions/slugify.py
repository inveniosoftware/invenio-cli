# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

from jinja2.ext import Extension
from slugify import slugify as pyslugify

class SlugifyExtension(Extension):
    """Jinja2 Extension to slugify string."""

    def __init__(self, environment):
        """Jinja2 Extension constructor."""
        super(SlugifyExtension, self).__init__(environment)

        def slugify(value, **kwargs):
            """Slugifies the value."""
            return pyslugify(value, **kwargs)

        environment.filters['slugify'] = slugify
