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

"""Constants."""


import os
from pathlib import Path

from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_ethereum.ethereum import (
    DEFAULT_EIP1559_STRATEGY,
    DEFAULT_GAS_STATION_STRATEGY,
)

from aea.configurations.constants import PRIVATE_KEY_PATH_SCHEMA
from aea.crypto.ledger_apis import ETHEREUM_DEFAULT_ADDRESS, ETHEREUM_DEFAULT_CHAIN_ID


DATA_DIR = Path(__file__).parent / "data"

ETHEREUM_PRIVATE_KEY_FILE = PRIVATE_KEY_PATH_SCHEMA.format(EthereumCrypto.identifier)
ETHEREUM_PRIVATE_KEY_TWO_FILE = "ethereum_private_key_two.txt"

ETHEREUM_ADDRESS_ONE = "0x46F415F7BF30f4227F98def9d2B22ff62738fD68"
ETHEREUM_ADDRESS_TWO = "0x7A1236d5195e31f1F573AD618b2b6FEFC85C5Ce6"

ETHEREUM_PRIVATE_KEY_PATH = os.path.join(DATA_DIR, ETHEREUM_PRIVATE_KEY_FILE)
ETHEREUM_PRIVATE_KEY_TWO_PATH = os.path.join(DATA_DIR, ETHEREUM_PRIVATE_KEY_TWO_FILE)

ETHEREUM_TESTNET_CONFIG = {
    "address": ETHEREUM_DEFAULT_ADDRESS,
    "chain_id": ETHEREUM_DEFAULT_CHAIN_ID,
    "default_gas_price_strategy": "gas_station",
    "gas_price_strategies": {
        "gas_station": DEFAULT_GAS_STATION_STRATEGY,
        "eip1559": DEFAULT_EIP1559_STRATEGY,
    },
}

FUNDED_ETH_PRIVATE_KEY_1 = (
    "0xa337a9149b4e1eafd6c21c421254cf7f98130233595db25f0f6f0a545fb08883"
)
FUNDED_ETH_PRIVATE_KEY_2 = (
    "0x04b4cecf78288f2ab09d1b4c60219556928f86220f0fb2dcfc05e6a1c1149dbf"
)
FUNDED_ETH_PRIVATE_KEY_3 = (
    "0x6F611408F7EF304947621C51A4B7D84A13A2B9786E9F984DA790A096E8260C64"
)
