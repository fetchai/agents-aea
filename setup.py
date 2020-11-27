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
import os
import re
from typing import Dict

from setuptools import find_packages, setup

PACKAGE_NAME = "aea"


def get_all_extras() -> Dict:

    cosmos_ledger_deps = ["ecdsa==0.15", "bech32==1.2.0"]

    fetch_ledger_deps = cosmos_ledger_deps

    ethereum_ledger_deps = [
        "web3==5.12.0",
        "ipfshttpclient==0.6.1",
        "eth-account==0.5.2",
    ]

    crypto_deps = [*fetch_ledger_deps, *ethereum_ledger_deps, *cosmos_ledger_deps]

    cli_deps = [
        "click",
        "pyyaml>=4.2b1",
        "jsonschema>=3.0.0",
        "python-dotenv",
        *crypto_deps,
    ]

    cli_gui = ["flask", "connexion[swagger-ui]>=2.4.0", "docker", *cli_deps]

    extras = {
        "cli": cli_deps,
        "cli_gui": cli_gui,
        "fetch": fetch_ledger_deps,
        "ethereum": ethereum_ledger_deps,
        "cosmos": cosmos_ledger_deps,
        "crypto": crypto_deps,
    }

    # add "all" extras
    extras["all"] = list(set(dep for e in extras.values() for dep in e))
    return extras


all_extras = get_all_extras()

base_deps = [
    *all_extras.get("crypto", []),
    "base58>=1.0.3",
    "jsonschema>=3.0.0",
    "packaging>=20.3",
    "semver>=2.9.1",
    "protobuf==3.13.0",
    "pymultihash==0.8.2",
    "pyyaml>=4.2b1",
    "requests>=2.22.0",
]

here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, PACKAGE_NAME, "__version__.py"), "r") as f:
    exec(f.read(), about)


def parse_readme():
    with open("README.md", "r") as f:
        readme = f.read()

    # replace relative links of images
    raw_url_root = "https://raw.githubusercontent.com/fetchai/agents-aea/master/"
    replacement = raw_url_root + r"\g<0>"
    readme = re.sub(r"(?<=<img src=\")(/.*)(?=\")", replacement, readme, re.DOTALL)

    header = re.search("<h1.*?(?=## )", readme, re.DOTALL).group(0)
    get_started = re.search("## Get started.*?(?=## )", readme, re.DOTALL).group(0)
    cite = re.search("## Cite.*$", readme, re.DOTALL).group(0)
    return "\n".join([header, get_started, cite])


setup(
    name=about["__title__"],
    description=about["__description__"],
    version=about["__version__"],
    author=about["__author__"],
    url=about["__url__"],
    long_description=parse_readme(),
    long_description_content_type="text/markdown",
    package_data={"aea": ["py.typed"]},
    packages=find_packages(include=["aea*"]),
    classifiers=[
        "Environment :: Console",
        "Environment :: Web Environment",
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: Microsoft",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Topic :: Communications",
        "Topic :: Internet",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development",
        "Topic :: System",
    ],
    install_requires=base_deps,
    tests_require=["tox"],
    extras_require=all_extras,
    entry_points={"console_scripts": ["aea=aea.cli:cli"]},
    zip_safe=False,
    include_package_data=True,
    license=about["__license__"],
    python_requires=">=3.6",
    keywords="aea autonomous-economic-agents agent-framework multi-agent-systems multi-agent cryptocurrency cryptocurrencies dezentralized dezentralized-network fetch-ai",
    project_urls={
        "Bug Reports": "https://github.com/fetchai/agents-aea/issues",
        "Source": "https://github.com/fetchai/agents-aea",
    },
)
