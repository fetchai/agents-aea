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

import time
from unittest.mock import MagicMock

import pytest

from aea.crypto.cosmos import CosmosApi, CosmosCrypto

from ..conftest import COSMOS_PRIVATE_KEY_PATH, COSMOS_TESTNET_CONFIG


def test_creation():
    """Test the creation of the crypto_objects."""
    assert CosmosCrypto(), "Did not manage to initialise the crypto module"
    assert CosmosCrypto(
        COSMOS_PRIVATE_KEY_PATH
    ), "Did not manage to load the cosmos private key"


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
    account = CosmosCrypto(COSMOS_PRIVATE_KEY_PATH)
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
    account = CosmosCrypto(COSMOS_PRIVATE_KEY_PATH)
    account.dump(MagicMock())


def test_api_creation():
    """Test api instantiation."""
    assert CosmosApi(**COSMOS_TESTNET_CONFIG), "Failed to initialise the api"


def test_api_none():
    """Test the "api" of the cryptoApi is none."""
    cosmos_api = CosmosApi(**COSMOS_TESTNET_CONFIG)
    assert cosmos_api.api is None, "The api property is not None."


@pytest.mark.network
def test_get_balance():
    """Test the balance is zero for a new account."""
    cosmos_api = CosmosApi(**COSMOS_TESTNET_CONFIG)
    cc = CosmosCrypto()
    balance = cosmos_api.get_balance(cc.address)
    assert balance == 0, "New account has a positive balance."
    cc = CosmosCrypto(private_key_path=COSMOS_PRIVATE_KEY_PATH)
    balance = cosmos_api.get_balance(cc.address)
    assert balance > 0, "Existing account has no balance."


@pytest.mark.network
def test_transfer():
    """Test transfer of wealth."""

    def try_transact(cc1, cc2, amount) -> str:
        attempts = 0
        while attempts < 3:
            fee = 1000
            tx_digest = cosmos_api.transfer(cc1, cc2.address, amount, fee)
            assert tx_digest is not None, "Failed to submit transfer!"
            not_settled = True
            elapsed_time = 0
            while not_settled and elapsed_time < 20:
                elapsed_time += 2
                time.sleep(2)
                is_settled = cosmos_api.is_transaction_settled(tx_digest)
                not_settled = not is_settled
            is_settled = cosmos_api.is_transaction_settled(tx_digest)
            if is_settled:
                attempts = 3
            else:
                attempts += 1
        assert is_settled, "Failed to complete tx on 3 attempts!"
        return tx_digest

    cosmos_api = CosmosApi(**COSMOS_TESTNET_CONFIG)
    cc1 = CosmosCrypto(private_key_path=COSMOS_PRIVATE_KEY_PATH)
    cc2 = CosmosCrypto()
    amount = 10000
    tx_digest = try_transact(cc1, cc2, amount)
    # TODO remove requirement for "" tx nonce stub
    is_valid = cosmos_api.is_transaction_valid(
        tx_digest, cc2.address, cc1.address, "", amount
    )
    assert is_valid, "Failed to settle tx correctly!"
