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

"""Setup script for "cosmos_crypto" package."""

from setuptools import find_packages, setup


setup(
    name="cosmos_crypto",
    version="0.1.0",
    author="Fetch.AI Limited",
    license="Apache-2.0",
    description="Python package wrapping the public and private key cryptography and ledger api of Cosmos.",
    packages=find_packages(include=["cosmos_crypto*"]),
    install_requires=["aea>=0.8.0,<0.9.0", "ecdsa==0.15", "bech32==1.2.0"],
    entry_points={
        "aea.cryptos": ["cosmos = cosmos_crypto:CosmosCrypto"],
        "aea.ledger_apis": ["cosmos = cosmos_crypto:CosmosApi"],
        "aea.faucet_apis": ["cosmos = cosmos_crypto:CosmosFaucetApi"]
    },
)
