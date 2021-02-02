#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""Setup script for "fetchai_crypto" package."""

import os

from setuptools import find_packages, setup


here = os.path.abspath(os.path.dirname(__file__))
plugin_dir = os.path.abspath(os.path.join(here, ".."))

setup(
    name="fetchai_crypto",
    version="0.1.0",
    author="Fetch.AI Limited",
    license="Apache-2.0",
    description="Python package wrapping the public and private key cryptography and ledger API of Fetch.AI.",
    packages=find_packages(include=["fetchai_crypto*"]),
    install_requires=[
        "aea>=0.9.0,<0.10.0",
        "ecdsa==0.15",
        "cosmos_crypto>=0.1.0,<0.2.0",
    ],
    tests_require=["pytest"],
    entry_points={
        "aea.cryptos": ["fetchai = fetchai_crypto:FetchAICrypto"],
        "aea.ledger_apis": ["fetchai = fetchai_crypto:FetchAIApi"],
        "aea.faucet_apis": ["fetchai = fetchai_crypto:FetchAIFaucetApi"],
    },
)
