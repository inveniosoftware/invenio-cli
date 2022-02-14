# -*- coding: utf-8 -*-
#
# Copyright (C) 2019-2020 CERN.
# Copyright (C) 2019-2020 Northwestern University.
# Copyright (C) 2021      TU Wien.
#
# Invenio-Cli is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module to ease the creation and management of applications."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'pytest-invenio>=1.4.0',
]

extras_require = {
    'docs': [
        'Sphinx==4.2.0',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for reqs in extras_require.values():
    extras_require['all'].extend(reqs)


install_requires = [
    'cookiecutter>=1.7.1,<1.8.0',
    'click>=7.1.1,<8.0',
    'click-default-group>=1.2.2,<2.0.0',
    'docker>=4.1.0,<6.0.0',
    'pipenv>=2020.6.2',
    'PyYAML>=5.1.2',
    'pynpm>=0.1.2',
    # virtualenv v20.13.1 ships with embedded setuptools 60.x, which means
    # that "invenio-cli install" will by default create a new virtual
    # environment with setuptools 60.x installed. celery v5.2.3 ships with a
    # dependency on setuptools>=59.1.1,<59.7.0 due to breaking changes
    # introduced in setuptools 60.x. pipenv or pip resolver does not properly
    # respect the dependency from celery and thus does not install a
    # compatible setuptools version leading to a ContextualVersionConflict
    # once running any command.
    # Once celery v5.2.4 is out, we can remove the pin again.
    'virtualenv>=20.0.35,<=20.13.0',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_cli', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-cli',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio-cli',
    license='MIT',
    author='CERN & Northwestern University',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-cli',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'console_scripts': [
            'invenio-cli = invenio_cli.cli.cli:invenio_cli',
        ]
    },
    extras_require=extras_require,
    install_requires=install_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Development Status :: 3 - Alpha',
    ],
)
