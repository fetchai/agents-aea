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

"""This module contains the tests of the ethereum module."""

import os
import time
from unittest.mock import MagicMock

from aea.crypto.cosmos import CosmosApi, CosmosCrypto

from ..conftest import ROOT_DIR

PRIVATE_KEY_PATH = os.path.join(ROOT_DIR, "tests/data/cosmos_private_key.txt")
TESTNET_CONFIG = {"address": "http://aea-testnet.sandbox.fetch-ai.com:1317"}


def test_creation():
    """Test the creation of the crypto_objects."""
    assert CosmosCrypto(), "Managed to initialise the crypto module"
    assert CosmosCrypto(PRIVATE_KEY_PATH), "Managed to load the cosmos private key"
    assert CosmosCrypto("./"), "Managed to create a new cosmos private key"


def test_initialization():
    """Test the initialisation of the variables."""
    account = CosmosCrypto()
    assert account.entity is not None, "The property must return the account."
    assert (
        account.address is not None
    ), "After creation the display address must not be None"
    assert (
        account.public_key is not None
    ), "After creation the public key must no be None"


def test_sign_and_recover_message():
    """Test the signing and the recovery function for the eth_crypto."""
    account = CosmosCrypto(PRIVATE_KEY_PATH)
    sign_bytes = account.sign_message(message=b"hello")
    assert len(sign_bytes) > 0, "The len(signature) must not be 0"
    recovered_addresses = account.recover_message(
        message=b"hello", signature=sign_bytes
    )
    assert (
        account.address in recovered_addresses
    ), "Failed to recover the correct address."


def test_dump_positive():
    """Test dump."""
    account = CosmosCrypto(PRIVATE_KEY_PATH)
    account.dump(MagicMock())


def test_api_creation():
    """Test api instantiation."""
    assert CosmosApi(**TESTNET_CONFIG), "Managed to initialise the api"


def test_transfer():
    """Test transfer of wealth."""
    cosmos_api = CosmosApi(**TESTNET_CONFIG)
    cc1 = CosmosCrypto(private_key_path=PRIVATE_KEY_PATH)
    cc2 = CosmosCrypto()
    amount = 10000
    fee = 1000
    tx_digest = cosmos_api.transfer(cc1, cc2.address, amount, fee)
    assert tx_digest is not None, "Failed to submit transfer!"
    time.sleep(2.0)
    # TODO remove requirement for "" tx nonce stub
    is_valid = cosmos_api.is_transaction_valid(
        tx_digest, cc2.address, cc1.address, "", amount
    )
    assert is_valid, "Failed to complete tx!"
