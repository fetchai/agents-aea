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

import hashlib
import os
import time
from unittest.mock import MagicMock

import pytest

from aea.crypto.ethereum import EthereumApi, EthereumCrypto

from ..conftest import ROOT_DIR

PRIVATE_KEY_PATH = os.path.join(ROOT_DIR, "tests/data/eth_private_key.txt")
TESTNET_CONFIG = {
    "address": "https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe",
    "gas_price": 50,
}


def test_creation():
    """Test the creation of the crypto_objects."""
    assert EthereumCrypto(), "Managed to initialise the eth_account"
    assert EthereumCrypto(PRIVATE_KEY_PATH), "Managed to load the eth private key"
    assert EthereumCrypto("./"), "Managed to create a new eth private key"


def test_initialization():
    """Test the initialisation of the variables."""
    account = EthereumCrypto()
    assert account.entity is not None, "The property must return the account."
    assert (
        account.address is not None and type(account.address) == str
    ), "After creation the display address must not be None"
    assert (
        account.public_key is not None and type(account.public_key) == str
    ), "After creation the public key must no be None"
    assert account.entity is not None, "After creation the entity must no be None"


def test_derive_address():
    """Test the get_address_from_public_key method"""
    account = EthereumCrypto()
    address = account.get_address_from_public_key(account.public_key)
    assert account.address == address, "Address derivation incorrect"


def test_sign_and_recover_message():
    """Test the signing and the recovery function for the eth_crypto."""
    account = EthereumCrypto(PRIVATE_KEY_PATH)
    sign_bytes = account.sign_message(message=b"hello")
    assert len(sign_bytes) > 0, "The len(signature) must not be 0"
    recovered_addresses = account.recover_message(
        message=b"hello", signature=sign_bytes
    )
    assert len(recovered_addresses) == 1, "Wrong number of addresses recovered."
    assert (
        recovered_addresses[0] == account.address
    ), "Failed to recover the correct address."


def test_sign_and_recover_message_deprecated():
    """Test the signing and the recovery function for the eth_crypto."""
    account = EthereumCrypto(PRIVATE_KEY_PATH)
    message = b"hello"
    message_hash = hashlib.sha256(message).digest()
    sign_bytes = account.sign_message(message=message_hash, is_deprecated_mode=True)
    assert len(sign_bytes) > 0, "The len(signature) must not be 0"
    recovered_addresses = account.recover_message(
        message=message_hash, signature=sign_bytes, is_deprecated_mode=True
    )
    assert len(recovered_addresses) == 1, "Wrong number of addresses recovered."
    assert (
        recovered_addresses[0] == account.address
    ), "Failed to recover the correct address."


def test_dump_positive():
    """Test dump."""
    account = EthereumCrypto(PRIVATE_KEY_PATH)
    account.dump(MagicMock())


def test_api_creation():
    """Test api instantiation."""
    assert EthereumApi(**TESTNET_CONFIG), "Failed to initialise the api"


def test_api_none():
    """Test the "api" of the cryptoApi is none."""
    eth_api = EthereumApi(**TESTNET_CONFIG)
    assert eth_api.api is not None, "The api property is None."


@pytest.mark.network
def test_get_balance():
    """Test the balance is zero for a new account."""
    ethereum_api = EthereumApi(**TESTNET_CONFIG)
    ec = EthereumCrypto()
    balance = ethereum_api.get_balance(ec.address)
    assert balance == 0, "New account has a positive balance."
    ec = EthereumCrypto(private_key_path=PRIVATE_KEY_PATH)
    balance = ethereum_api.get_balance(ec.address)
    assert balance > 0, "Existing account has no balance."


@pytest.mark.network
def test_transfer():
    """Test transfer of wealth."""
    ethereum_api = EthereumApi(**TESTNET_CONFIG)
    ec1 = EthereumCrypto(private_key_path=PRIVATE_KEY_PATH)
    ec2 = EthereumCrypto()
    amount = 40000
    fee = 30000
    tx_nonce = ethereum_api.generate_tx_nonce(ec2.address, ec1.address)
    tx_digest = ethereum_api.transfer(
        ec1, ec2.address, amount, fee, tx_nonce, chain_id=3
    )
    assert tx_digest is not None, "Failed to submit transfer!"
    not_settled = True
    elapsed_time = 0
    while not_settled and elapsed_time < 60:
        elapsed_time += 2
        time.sleep(2)
        is_settled = ethereum_api.is_transaction_settled(tx_digest)
        not_settled = not is_settled
    assert is_settled, "Failed to complete tx!"
    is_valid = ethereum_api.is_transaction_valid(
        tx_digest, ec2.address, ec1.address, tx_nonce, amount
    )
    assert is_valid, "Failed to settle tx correctly!"
