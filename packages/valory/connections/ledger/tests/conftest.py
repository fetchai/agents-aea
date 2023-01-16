# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

"""Test confiugurations for the package."""
# pylint: skip-file

import logging
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator, cast
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_ethereum.test_tools.constants import (
    ETHEREUM_TESTNET_CONFIG as _DEFAULT_ETHEREUM_TESTNET_CONFIG,
)
from aea_ledger_ethereum.test_tools.fixture_helpers import (
    DEFAULT_GANACHE_ADDR,
    DEFAULT_GANACHE_PORT,
)

from aea.configurations.base import ComponentType, ContractConfig
from aea.configurations.constants import DEFAULT_LEDGER
from aea.configurations.loader import load_component_configuration
from aea.connections.base import Connection
from aea.contracts.base import Contract, contract_registry
from aea.crypto.ledger_apis import DEFAULT_LEDGER_CONFIGS, LedgerApi
from aea.crypto.registries import ledger_apis_registry, make_crypto
from aea.crypto.wallet import CryptoStore
from aea.identity.base import Identity


PACKAGE_DIR = Path(__file__).parent.parent

DEFAULT_ETHEREUM_TESTNET_CONFIG = {
    **_DEFAULT_ETHEREUM_TESTNET_CONFIG,
    "default_gas_price_strategy": "eip1559",
}


def get_register_contract(directory: Path) -> Contract:
    """Get and register the erc1155 contract package."""
    configuration = load_component_configuration(ComponentType.CONTRACT, directory)
    configuration._directory = directory  # pylint: disable=protected-access
    configuration = cast(ContractConfig, configuration)

    if str(configuration.public_id) not in contract_registry.specs:
        # load contract into sys modules
        Contract.from_config(configuration)

    contract = contract_registry.make(str(configuration.public_id))
    return contract


@pytest.fixture()
def ganache_addr() -> str:
    """Get the ganache addr"""
    return DEFAULT_GANACHE_ADDR


@pytest.fixture()
def ganache_port() -> int:
    """Get the ganache port"""
    return DEFAULT_GANACHE_PORT


@pytest.fixture(scope="function")
def ethereum_testnet_config(ganache_addr: str, ganache_port: int) -> Dict:
    """Get Ethereum ledger api configurations using Ganache."""
    new_uri = f"{ganache_addr}:{ganache_port}"
    new_config = DEFAULT_ETHEREUM_TESTNET_CONFIG.copy()
    new_config["address"] = new_uri
    return new_config


@pytest.fixture(scope="function")
def update_default_ethereum_ledger_api(ethereum_testnet_config: Dict) -> Generator:
    """Change temporarily default Ethereum ledger api configurations to interact with local Ganache."""
    old_config = DEFAULT_LEDGER_CONFIGS.pop(EthereumCrypto.identifier)
    DEFAULT_LEDGER_CONFIGS[EthereumCrypto.identifier] = ethereum_testnet_config
    yield
    DEFAULT_LEDGER_CONFIGS.pop(EthereumCrypto.identifier)
    DEFAULT_LEDGER_CONFIGS[EthereumCrypto.identifier] = old_config


def make_ledger_api_connection(
    ethereum_testnet_config: Dict = DEFAULT_ETHEREUM_TESTNET_CONFIG,
) -> Connection:
    """Make a connection."""
    crypto = make_crypto(DEFAULT_LEDGER)
    identity = Identity("name", crypto.address, crypto.public_key)
    crypto_store = CryptoStore()
    directory = PACKAGE_DIR
    connection = Connection.from_dir(
        str(directory),
        data_dir=MagicMock(),
        identity=identity,
        crypto_store=crypto_store,
    )
    connection = cast(Connection, connection)
    connection._logger = logging.getLogger("packages.valory.connections.ledger")

    # use testnet config
    connection.configuration.config.get("ledger_apis", {})[
        "ethereum"
    ] = ethereum_testnet_config

    connection.request_retry_attempts = 1  # type: ignore
    connection.request_retry_attempts = 2  # type: ignore
    return connection


@pytest_asyncio.fixture()
async def ledger_apis_connection(
    request: Any, ethereum_testnet_config: Dict
) -> AsyncGenerator:
    """Make a connection."""
    connection = make_ledger_api_connection(ethereum_testnet_config)
    await connection.connect()
    yield connection
    await connection.disconnect()


@pytest.fixture()
def ledger_api(
    ethereum_testnet_config: Dict,
) -> Generator[LedgerApi, None, None]:
    """Ledger api fixture."""
    ledger_id, config = EthereumCrypto.identifier, ethereum_testnet_config
    api = ledger_apis_registry.make(ledger_id, **config)
    yield api
