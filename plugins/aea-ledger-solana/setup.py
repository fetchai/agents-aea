#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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

"""Setup script for "aea_ledger_solana" package."""

from setuptools import find_packages, setup


setup(
    name="open-aea-ledger-solana",
    version="1.32.0",
    author="dassy23",
    license="Apache-2.0",
    description="Python package wrapping the public and private key cryptography and ledger api of solana.",
    long_description="Python package wrapping the public and private key cryptography and ledger api of solana.",
    long_description_content_type="text/markdown",
    packages=find_packages(include=["aea_ledger_solana*"]),
    package_data={},
    install_requires=[
        "open-aea>=1.0.0, <2.0.0",
        "solders==0.14.0",
        "cryptography",
        "PyNaCl==1.5.0",
        "anchorpy @ git+https://github.com/kevinheavey/anchorpy.git@a3cc292574679bae1610e01ab69161b6614bca92",
        "solana==0.29.2",
    ],
    tests_require=["pytest"],
    entry_points={
        "aea.cryptos": ["solana = aea_ledger_solana:SolanaCrypto"],
        "aea.ledger_apis": ["solana = aea_ledger_solana:SolanaApi"],
        "aea.faucet_apis": ["solana = aea_ledger_solana:SolanaFaucetApi"],
    },
    classifiers=[
        "Environment :: Console",
        "Environment :: Web Environment",
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: Microsoft",
        "Operating System :: Unix",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Communications",
        "Topic :: Internet",
        "Topic :: Software Development",
    ],
)
