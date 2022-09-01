# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""Fixture helpers"""

from contextlib import contextmanager
from pathlib import Path
from typing import Dict

import pytest
from aea_ledger_ethereum.test_tools.constants import (
    ETHEREUM_PRIVATE_KEY_PATH,
    FUNDED_ETH_PRIVATE_KEY_1,
    FUNDED_ETH_PRIVATE_KEY_2,
    FUNDED_ETH_PRIVATE_KEY_3,
)
from aea_ledger_ethereum.test_tools.docker_images import GanacheDockerImage

from aea.test_tools.docker_image import launch_image
from aea.test_tools.network import LOCALHOST


DEFAULT_GANACHE_ADDR = LOCALHOST.geturl()
DEFAULT_GANACHE_PORT = 8545
DEFAULT_GANACHE_CHAIN_ID = 1337
DEFAULT_AMOUNT = 1000000000000000000000

GANACHE_CONFIGURATION = dict(
    accounts_balances=[
        (FUNDED_ETH_PRIVATE_KEY_1, DEFAULT_AMOUNT),
        (FUNDED_ETH_PRIVATE_KEY_2, DEFAULT_AMOUNT),
        (FUNDED_ETH_PRIVATE_KEY_3, DEFAULT_AMOUNT),
        (Path(ETHEREUM_PRIVATE_KEY_PATH).read_text().strip(), DEFAULT_AMOUNT),
    ],
)


@contextmanager
def _ganache_context(
    ganache_configuration: Dict,
    ganache_addr: str = DEFAULT_GANACHE_ADDR,
    ganache_port: int = DEFAULT_GANACHE_PORT,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    import docker  # pylint: disable=import-outside-toplevel,import-error

    client = docker.from_env()
    image = GanacheDockerImage(
        client, ganache_addr, ganache_port, config=ganache_configuration
    )
    yield from launch_image(image, timeout=timeout, max_attempts=max_attempts)


@pytest.fixture(scope="class")
def ganache(
    ganache_addr=DEFAULT_GANACHE_ADDR,
    ganache_port=DEFAULT_GANACHE_PORT,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    """Launch the Ganache image."""
    with _ganache_context(
        GANACHE_CONFIGURATION.copy(), ganache_addr, ganache_port, timeout, max_attempts
    ) as image:
        yield image
