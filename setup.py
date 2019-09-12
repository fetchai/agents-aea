#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------
import importlib
import os
import re
from typing import List, Dict

from setuptools import setup, find_packages

PACKAGE_NAME = "aea"


def get_aea_extras() -> Dict[str, List[str]]:
    """Parse extra dependencies from aea channels and protocols."""
    result = {}

    # parse channel dependencies
    channel_module = importlib.import_module("aea.channel")
    channel_dependencies = {k.split("_")[0] + "-channel": v for k, v in vars(channel_module).items() if re.match(".+_dependencies", k)}
    result.update(channel_dependencies)

    # parse protocols dependencies
    protocols_module = importlib.import_module("aea.protocols")
    protocols_dependencies = {k.split("_")[0] + "-protocol": v for k, v in vars(protocols_module).items() if re.match(".+_dependencies", k)}
    result.update(protocols_dependencies)

    return result


def get_all_extras() -> Dict:
    extras = {
        "cli": [
            "click",
            "click_log",
            "PyYAML"
        ],
    }
    extras.update(get_aea_extras())

    # add "all" extras
    extras["all"] = list(set(dep for e in extras.values() for dep in e))
    return extras


here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, PACKAGE_NAME, '__version__.py'), 'r') as f:
    exec(f.read(), about)

with open('README.md', 'r') as f:
    readme = f.read()

setup(
    name=about['__title__'],
    description=about['__description__'],
    version=about['__version__'],
    author=about['__author__'],
    url=about['__url__'],
    long_description=readme,
    packages=find_packages(include=["aea*"]),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    install_requires=[
        "cryptography",
        "base58"
    ],
    tests_require=["tox"],
    extras_require=get_all_extras(),
    entry_points={
        'console_scripts': ["aea=aea.cli:cli"],
    },
    license=about['__license__'],
)
