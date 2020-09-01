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

"""
This script takes all the protocol specification (scraped from the protocol README)
and calls the `aea generate protocol` command.
"""
import subprocess
import sys
from pathlib import Path


PROTOCOL_PACKAGES_PATH = [
    Path("aea", "protocols", "default"),
    Path("aea", "protocols", "signing"),
    Path("aea", "protocols", "state_update"),
    Path("packages", "fetchai", "protocols", "contract_api"),
    Path("packages", "fetchai", "protocols", "fipa"),
    Path("packages", "fetchai", "protocols", "gym"),
    Path("packages", "fetchai", "protocols", "http"),
    Path("packages", "fetchai", "protocols", "ledger_api"),
    Path("packages", "fetchai", "protocols", "ml_trade"),
    Path("packages", "fetchai", "protocols", "oef_search"),
    Path("packages", "fetchai", "protocols", "tac"),
]


def install(package: str) -> int:
    """
    Install a PyPI package by calling pip.

    :param package: the package name and version specifier.
    :return: the return code.
    """
    return subprocess.check_call(  # nosec
        [sys.executable, "-m", "aea", "generate", "protocol", package]
    )


def main():
    """Run the script."""


if __name__ == "__main__":
    main()
