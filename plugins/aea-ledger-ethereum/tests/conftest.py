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

"""Conftest module for Pytest."""
import inspect
import logging
import os
import platform
import shutil
import tempfile
import time
from functools import wraps
from pathlib import Path
from typing import Callable, Generator

import docker
import pytest
from aea_ledger_ethereum import EthereumCrypto

from aea.configurations.constants import PRIVATE_KEY_PATH_SCHEMA

from tests.docker_image import DockerImage, GanacheDockerImage


CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
ROOT_DIR = os.path.join(CUR_PATH, "..")
MAX_FLAKY_RERUNS = 3
ETHEREUM = EthereumCrypto.identifier

ETHEREUM_PRIVATE_KEY_FILE = PRIVATE_KEY_PATH_SCHEMA.format(ETHEREUM)
ETHEREUM_PRIVATE_KEY_PATH = os.path.join(
    ROOT_DIR, "tests", "data", ETHEREUM_PRIVATE_KEY_FILE
)

ETHEREUM_DEFAULT_ADDRESS = "http://127.0.0.1:8545"
ETHEREUM_DEFAULT_CHAIN_ID = 1337
ETHEREUM_DEFAULT_CURRENCY_DENOM = "wei"
ETHEREUM_TESTNET_CONFIG = {"address": ETHEREUM_DEFAULT_ADDRESS}

# URL to local Ganache instance
DEFAULT_GANACHE_ADDR = "http://127.0.0.1"
DEFAULT_GANACHE_PORT = 8545
DEFAULT_GANACHE_CHAIN_ID = 1337
GAS_PRICE_API_KEY = ""

DEFAULT_AMOUNT = 1000000000000000000000
FUNDED_ETH_PRIVATE_KEY_1 = (
    "0xa337a9149b4e1eafd6c21c421254cf7f98130233595db25f0f6f0a545fb08883"
)
FUNDED_ETH_PRIVATE_KEY_2 = (
    "0x04b4cecf78288f2ab09d1b4c60219556928f86220f0fb2dcfc05e6a1c1149dbf"
)
FUNDED_ETH_PRIVATE_KEY_3 = (
    "0x6F611408F7EF304947621C51A4B7D84A13A2B9786E9F984DA790A096E8260C64"
)

logger = logging.getLogger(__name__)


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
def ethereum_private_key_file():
    """Pytest fixture to create a temporary Ethereum private key file."""
    crypto = EthereumCrypto()
    temp_dir = Path(tempfile.mkdtemp())
    try:
        temp_file = temp_dir / "private.key"
        temp_file.write_text(crypto.private_key)
        yield str(temp_file)
    finally:
        shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def ethereum_testnet_config(ganache_addr, ganache_port):
    """Get Ethereum ledger api configurations using Ganache."""
    new_uri = f"{ganache_addr}:{ganache_port}"
    new_config = {
        "address": new_uri,
        "chain_id": DEFAULT_GANACHE_CHAIN_ID,
        "denom": ETHEREUM_DEFAULT_CURRENCY_DENOM,
        "gas_price_api_key": GAS_PRICE_API_KEY,
    }
    return new_config


@pytest.fixture(scope="session")
def ganache_addr() -> str:
    """HTTP address to the Ganache node."""
    return DEFAULT_GANACHE_ADDR


@pytest.fixture(scope="session")
def ganache_port() -> int:
    """Port of the connection to the OEF Node to use during the tests."""
    return DEFAULT_GANACHE_PORT


@pytest.fixture(scope="session")
def ganache_configuration(ethereum_private_key_file):
    """Get the Ganache configuration for testing purposes."""
    return dict(
        accounts_balances=[
            (FUNDED_ETH_PRIVATE_KEY_1, DEFAULT_AMOUNT),
            (FUNDED_ETH_PRIVATE_KEY_2, DEFAULT_AMOUNT),
            (FUNDED_ETH_PRIVATE_KEY_3, DEFAULT_AMOUNT),
            (Path(ethereum_private_key_file).read_text().strip(), DEFAULT_AMOUNT),
        ],
    )


@pytest.mark.integration
@pytest.mark.ledger
@pytest.fixture(scope="session")
@action_for_platform("Linux", skip=False)
def ganache(
    ganache_configuration,
    ganache_addr,
    ganache_port,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    """Launch the Ganache image."""
    client = docker.from_env()
    image = GanacheDockerImage(
        client, "http://127.0.0.1", 8545, config=ganache_configuration
    )
    yield from _launch_image(image, timeout=timeout, max_attempts=max_attempts)


def _launch_image(
    image: DockerImage, timeout: float = 2.0, max_attempts: int = 10
) -> Generator:
    """
    Launch image.

    :param image: an instance of Docker image.
    :param timeout: timeout to launch
    :param max_attempts: max launch attempts
    :yield: image
    """
    image.check_skip()
    image.stop_if_already_running()
    container = image.create()
    container.start()
    logger.info(f"Setting up image {image.tag}...")
    success = image.wait(max_attempts, timeout)
    if not success:
        container.stop()
        container.remove()
        pytest.fail(f"{image.tag} doesn't work. Exiting...")
    else:
        logger.info("Done!")
        time.sleep(timeout)
        yield
        logger.info(f"Stopping the image {image.tag}...")
        container.stop()
        container.remove()
