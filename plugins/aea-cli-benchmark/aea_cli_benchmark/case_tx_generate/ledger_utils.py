# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""Ledger TX generation and processing benchmark."""
import time
from contextlib import contextmanager
from typing import List

import docker
from aea_cli_benchmark.case_tx_generate.docker_image import (
    DockerImage,
    FetchLedgerDockerImage,
    GanacheDockerImage,
)
from cosmpy.clients.signing_cosmwasm_client import SigningCosmWasmClient
from cosmpy.common.rest_client import RestClient
from cosmpy.crypto.address import Address as CosmpyAddress
from cosmpy.crypto.keypairs import PrivateKey
from cosmpy.protos.cosmos.base.v1beta1.coin_pb2 import Coin


FETCHD_INITIAL_TX_SLEEP = 6
GAS_PRICE_API_KEY = ""
DEFAULT_FETCH_LEDGER_ADDR = "http://127.0.0.1"
DEFAULT_FETCH_LEDGER_REST_PORT = 1317
DEFAULT_GANACHE_ADDR = "http://127.0.0.1"
DEFAULT_GANACHE_PORT = 8545
DEFAULT_GANACHE_CHAIN_ID = 1337


FUNDED_ETH_PRIVATE_KEY_1 = (
    "0xa337a9149b4e1eafd6c21c421254cf7f98130233595db25f0f6f0a545fb08883"
)

DEFAULT_AMOUNT = 1000000000000000000000
DEFAULT_FETCH_MNEMONIC = "gap bomb bulk border original scare assault pelican resemble found laptop skin gesture height inflict clinic reject giggle hurdle bubble soldier hurt moon hint"
DEFAULT_MONIKER = "test-node"
DEFAULT_GENESIS_ACCOUNT = "validator"
DEFAULT_DENOMINATION = "atestfet"
DEFAULT_FETCH_CHAIN_ID = "stargateworld-3"

FETCHD_CONFIGURATION = dict(
    mnemonic=DEFAULT_FETCH_MNEMONIC,
    moniker=DEFAULT_MONIKER,
    chain_id=DEFAULT_FETCH_CHAIN_ID,
    genesis_account=DEFAULT_GENESIS_ACCOUNT,
    denom=DEFAULT_DENOMINATION,
)
FUNDED_FETCHAI_PRIVATE_KEY_1 = (
    "bbaef7511f275dc15f47436d14d6d3c92d4d01befea073d23d0c2750a46f6cb3"
)
GANACHE_CONFIGURATION = dict(
    accounts_balances=[(FUNDED_ETH_PRIVATE_KEY_1, DEFAULT_AMOUNT)]
)


DEFAULT_FETCH_LEDGER_RPC_PORT = 26657
DEFAULT_FETCH_DOCKER_IMAGE_TAG = "fetchai/fetchd:0.8.4"


@contextmanager
def _fetchd_context(fetchd_configuration, timeout: float = 2.0, max_attempts: int = 20):
    client = docker.from_env()
    image = FetchLedgerDockerImage(
        client,
        DEFAULT_FETCH_LEDGER_ADDR,
        DEFAULT_FETCH_LEDGER_RPC_PORT,
        DEFAULT_FETCH_DOCKER_IMAGE_TAG,
        config=fetchd_configuration,
    )
    yield from _launch_image(image, timeout=timeout, max_attempts=max_attempts)


def _launch_image(image: DockerImage, timeout: float = 2.0, max_attempts: int = 10):
    """
    Launch image.

    :param image: an instance of Docker image.
    :param timeout:  timeout to wait docker image launched.
    :param max_attempts: max attempts to check docker image is up.
    :yield: None
    """
    image.check_skip()
    image.stop_if_already_running()
    container = image.create()
    container.start()
    success = image.wait(max_attempts, timeout)
    if not success:
        container.stop()
        container.remove()
        raise Exception(f"{image.tag} doesn't work. Exiting...")
    else:
        try:
            time.sleep(timeout)
            yield
        finally:
            container.stop()
            container.remove()


@contextmanager
def _ganache_context(
    ganache_configuration,
    ganache_addr=DEFAULT_GANACHE_ADDR,
    ganache_port=DEFAULT_GANACHE_PORT,
    timeout: float = 2.0,
    max_attempts: int = 10,
):
    client = docker.from_env()
    image = GanacheDockerImage(
        client, ganache_addr, ganache_port, config=ganache_configuration
    )
    yield from _launch_image(image, timeout=timeout, max_attempts=max_attempts)


def fund_accounts_from_local_validator(
    addresses: List[str], amount: int, denom: str = DEFAULT_DENOMINATION
):
    """Send funds to local accounts from the local genesis validator."""
    rest_client = RestClient(
        f"{DEFAULT_FETCH_LEDGER_ADDR}:{DEFAULT_FETCH_LEDGER_REST_PORT}"
    )
    pk = PrivateKey(bytes.fromhex(FUNDED_FETCHAI_PRIVATE_KEY_1))

    time.sleep(FETCHD_INITIAL_TX_SLEEP)
    client = SigningCosmWasmClient(pk, rest_client, DEFAULT_FETCH_CHAIN_ID)
    coins = [Coin(amount=str(amount), denom=denom)]

    for address in addresses:
        client.send_tokens(CosmpyAddress(address), coins)
