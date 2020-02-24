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
import glob
import importlib
import os
import re
from typing import List, Dict

from setuptools import setup, find_packages

PACKAGE_NAME = "aea"


def get_aea_extras() -> Dict[str, List[str]]:
    """Parse extra dependencies from aea channels and protocols."""
    result = {}

    # parse connections dependencies
    connection_module = importlib.import_module("aea.connections")
    connection_dependencies = {k.split("_")[0] + "-connection": v for k, v in vars(connection_module).items() if re.match(".+_dependencies", k)}
    result.update(connection_dependencies)

    # parse protocols dependencies
    protocols_module = importlib.import_module("aea.protocols")
    protocols_dependencies = {k.split("_")[0] + "-protocol": v for k, v in vars(protocols_module).items() if re.match(".+_dependencies", k)}
    result.update(protocols_dependencies)

    # parse skills dependencies
    skills_module = importlib.import_module("aea.skills")
    skills_dependencies = {k.split("_")[0] + "-skill": v for k, v in vars(skills_module).items() if re.match(".+_dependencies", k)}
    result.update(skills_dependencies)

    return result


def get_all_extras() -> Dict:

    fetch_ledger_deps = [
        "fetchai-ledger-api==1.0.0rc1"
    ]

    ethereum_ledger_deps = [
        "web3==5.2.2",
        "eth-account==0.4.0"
    ]

    crypto_deps = [
        *fetch_ledger_deps,
        *ethereum_ledger_deps
    ]

    cli_deps = [
        "click",
        "pyyaml>=4.2b1",
        "jsonschema>=3.0.0",
        "python-dotenv",
        *crypto_deps
    ]

    cli_gui = [
        "flask",
        "connexion[swagger-ui]>=2.4.0",
        "docker",
        *cli_deps
    ]

    extras = {
        "cli": cli_deps,
        "cli_gui": cli_gui,
        "fetch": fetch_ledger_deps,
        "ethereum": ethereum_ledger_deps,
        "crypto": crypto_deps
    }
    extras.update(get_aea_extras())

    # add "all" extras
    extras["all"] = list(set(dep for e in extras.values() for dep in e))
    return extras


all_extras = get_all_extras()

base_deps = [
   *all_extras.get("crypto", []),
    "pyyaml>=4.2b1",
    "jsonschema>=3.0.0",
    "protobuf",
    "watchdog"
]

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
    long_description_content_type='text/markdown',
    packages=find_packages(include=["aea*"]),
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    install_requires=base_deps,
    tests_require=["tox"],
    extras_require=all_extras,
    entry_points={
        'console_scripts': ["aea=aea.cli:cli"],
    },
    zip_safe=False,
    include_package_data=True,
    data_files=[
        (
            os.path.join("aea", "skills", "base", "schemas"),
            glob.glob(os.path.join("aea", "skills", "base", "schemas", "*.json"))
        ),
    ],
    license=about['__license__'],
    python_requires=">=3.6",
    keywords="aea autonomous-economic-agents agent-framework multi-agent-systems multi-agent cryptocurrency cryptocurrencies dezentralized dezentralized-network fetch-ai",
    project_urls={
        'Bug Reports': 'https://github.com/fetchai/agents-aea/issues',
        'Source': 'https://github.com/fetchai/agents-aea',
    },
)
