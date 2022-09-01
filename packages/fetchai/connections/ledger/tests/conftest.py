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

"""Conftest module."""
# pylint: skip-file

import logging
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock

import pytest
from aea_ledger_ethereum import DEFAULT_EIP1559_STRATEGY, EthereumCrypto
from aea_ledger_ethereum.test_tools.fixture_helpers import (
    DEFAULT_GANACHE_ADDR,
    DEFAULT_GANACHE_CHAIN_ID,
    DEFAULT_GANACHE_PORT,
)

from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection
from aea.crypto.ledger_apis import (
    DEFAULT_LEDGER_CONFIGS,
    ETHEREUM_DEFAULT_CURRENCY_DENOM,
)
from aea.crypto.registries import make_crypto
from aea.crypto.wallet import CryptoStore
from aea.identity.base import Identity


PACKAGE_DIR = Path(__file__).parent.parent


@pytest.fixture(scope="session")
def ethereum_testnet_config():
    """Get Ethereum ledger api configurations using Ganache."""
    new_uri = f"{DEFAULT_GANACHE_ADDR}:{DEFAULT_GANACHE_PORT}"
    new_config = {
        "address": new_uri,
        "chain_id": DEFAULT_GANACHE_CHAIN_ID,
        "denom": ETHEREUM_DEFAULT_CURRENCY_DENOM,
        "default_gas_price_strategy": "gas_station",
        "gas_price_strategies": {
            "eip1559": DEFAULT_EIP1559_STRATEGY,
            "gas_station": {
                "gas_price_api_key": "",
                "gas_price_strategy": "fast",
            },
        },
    }
    return new_config


@pytest.fixture(scope="function")
def update_default_ethereum_ledger_api(
    ethereum_testnet_config,
):  # pylint: disable=redefined-outer-name
    """Change temporarily default Ethereum ledger api configurations to interact with local Ganache."""
    old_config = DEFAULT_LEDGER_CONFIGS.pop(EthereumCrypto.identifier, None)
    DEFAULT_LEDGER_CONFIGS[EthereumCrypto.identifier] = ethereum_testnet_config
    yield
    DEFAULT_LEDGER_CONFIGS.pop(EthereumCrypto.identifier)
    DEFAULT_LEDGER_CONFIGS[EthereumCrypto.identifier] = old_config


@pytest.fixture()
async def ledger_apis_connection(
    request, ethereum_testnet_config
):  # pylint: disable=redefined-outer-name,unused-argument
    """Make a connection."""
    crypto = make_crypto(DEFAULT_LEDGER)
    identity = Identity("name", crypto.address, crypto.public_key)
    crypto_store = CryptoStore()
    connection = Connection.from_dir(
        PACKAGE_DIR, data_dir=MagicMock(), identity=identity, crypto_store=crypto_store
    )
    connection = cast(Connection, connection)
    connection._logger = logging.getLogger(
        "aea.packages.fetchai.connections.ledger"
    )  # pylint: disable=protected-access

    # use testnet config
    connection.configuration.config.get("ledger_apis", {})[
        "ethereum"
    ] = ethereum_testnet_config

    await connection.connect()
    yield connection
    await connection.disconnect()
