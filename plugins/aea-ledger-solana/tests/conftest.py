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

"""Conftest module for Pytest."""
import inspect
import logging
import os
import platform
import shutil
import tempfile
from functools import wraps
from pathlib import Path
from typing import Callable

import pytest
from aea_ledger_solana import SolanaCrypto

from aea.configurations.constants import PRIVATE_KEY_PATH_SCHEMA


CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
ROOT_DIR = os.path.join(CUR_PATH, "..")
MAX_FLAKY_RERUNS = 3
AIRDROP_AMOUNT = 1

SOLANA = SolanaCrypto.identifier

SOLANA_PRIVATE_KEY_FILE = PRIVATE_KEY_PATH_SCHEMA.format(SOLANA)

SOLANA_PRIVATE_KEY_PATH = os.path.join(
    ROOT_DIR, "tests", "data", SOLANA_PRIVATE_KEY_FILE
)

SOLANA_PRIVATE_KEY_FILE_1 = os.path.join(
    ROOT_DIR, "tests", "data", SOLANA_PRIVATE_KEY_FILE[:-4] + "_1" + ".txt"
)


SOLANA_DEFAULT_ADDRESS = "http://127.0.0.1:8899"
SOLANA_DEFAULT_CHAIN_ID = 420
SOLANA_DEFAULT_CURRENCY_DENOM = "lamports"
SOLANA_TESTNET_CONFIG = {"address": SOLANA_DEFAULT_ADDRESS}


logger = logging.getLogger(__name__)

PROGRAM_KEYPAIR_PATH = Path(ROOT_DIR, "tests", "data", "solana_private_key_program.txt")
PAYER_KEYPAIR_PATH = Path(ROOT_DIR, "tests", "data", "solana_private_key1.txt")
PLAYER1_KEYPAIR_PATH = Path(ROOT_DIR, "tests", "data", "solana_private_key1.txt")
PLAYER2_KEYPAIR_PATH = Path(ROOT_DIR, "tests", "data", "solana_private_key2.txt")


def action_for_platform(platform_name: str, skip: bool = True) -> Callable:
    """
    Decorate a pytest class or method to skip on certain platform.

    :param platform_name: check `platform.system()` for available platforms.
    :param skip: if True, the test will be skipped; if False, the test will be run ONLY on the chosen platform.
    :return: decorated object
    """

    # for docstyle.
    def decorator(pytest_func):
        """
        For the sake of clarity, assume the chosen platform for the action is "Windows".

        If the following condition is true:
          - the current system is not Windows (is_different) AND we want to skip it (skip)
         OR
          - the current system is Windows (not is_different) AND we want to run only on it (not skip)
        we run the test, else we skip the test.

        logically, the condition is a boolean equivalence
        between the variables "is_different" and "skip"
        Hence, the condition becomes:

        :param pytest_func: the pytest function to wrap
        :return: the wrapped function
        """
        is_different = platform.system() != platform_name
        if is_different is skip:
            return pytest_func

        def action(*args, **kwargs):
            if skip:
                pytest.skip(
                    f"Skipping the test since it doesn't work on {platform_name}."
                )
            else:
                pytest.skip(
                    f"Skipping the test since it works only on {platform_name}."
                )

        if isinstance(pytest_func, type):
            return type(
                pytest_func.__name__,
                (pytest_func,),
                {
                    "setup_class": action,
                    "setup": action,
                    "setUp": action,
                    "_skipped": True,
                },
            )

        @wraps(pytest_func)
        def wrapper(*args, **kwargs):  # type: ignore
            action(*args, **kwargs)

        return wrapper

    return decorator


@pytest.fixture(scope="session")
def solana_private_key_file():
    """Pytest fixture to create a temporary Solana private key file."""
    crypto = SolanaCrypto()
    temp_dir = Path(tempfile.mkdtemp())
    try:
        temp_file = temp_dir / "private_key.txt"
        temp_file.write_text(crypto.private_key)
        yield str(temp_file)

    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def solana_testnet_config(ganache_addr, ganache_port):
    """Get Solana ledger api configurations using Ganache."""
    new_uri = f"{ganache_addr}:{ganache_port}"
    new_config = {
        "address": new_uri,
        "chain_id": SOLANA_DEFAULT_CHAIN_ID,
        "denom": SOLANA_DEFAULT_CURRENCY_DENOM,
    }
    return new_config
