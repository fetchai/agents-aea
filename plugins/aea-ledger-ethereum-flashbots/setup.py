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

"""Setup script for "aea_ledger_ethereum_flashbots" package."""

from setuptools import find_packages, setup


setup(
    name="open-aea-ledger-ethereum-flashbots",
    version="1.32.0",
    author="Valory AG",
    license="Apache-2.0",
    description="Python package extending the default open-aea ethereum ledger plugin to add support for flashbots.",
    long_description=(
        "Python package extending the default open-aea ethereum ledger plugin to add support for flashbots."
    ),
    long_description_content_type="text/markdown",
    packages=find_packages(include=["aea_ledger_ethereum_flashbots*"]),
    package_data={
        "aea_ledger_ethereum_flashbots": [
            "py.typed",
        ]
    },
    python_requires=">=3.9,<4.0",
    install_requires=[
        "open-aea-ledger-ethereum~=1.32.0",
        "flashbots==1.1.1",
    ],
    tests_require=["pytest"],
    entry_points={
        "aea.cryptos": [
            "ethereum_flashbots = aea_ledger_ethereum_flashbots:EthereumFlashbotCrypto"
        ],
        "aea.ledger_apis": [
            "ethereum_flashbots = aea_ledger_ethereum_flashbots:EthereumFlashbotApi"
        ],
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
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Communications",
        "Topic :: Internet",
        "Topic :: Software Development",
    ],
)
