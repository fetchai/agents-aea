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

from unittest.mock import MagicMock

import pytest

from aea.crypto.fetchai import FetchAIApi, FetchAICrypto

from ..conftest import FETCHAI_PRIVATE_KEY_PATH, FETCHAI_TESTNET_CONFIG


def test_initialisation():
    """Test the initialisation of the the fet crypto."""
    fet_crypto = FetchAICrypto()
    assert (
        fet_crypto.public_key is not None
    ), "Public key must not be None after Initialisation"
    assert (
        fet_crypto.address is not None
    ), "Address must not be None after Initialisation"
    assert FetchAICrypto(
        FETCHAI_PRIVATE_KEY_PATH
    ), "Couldn't load the fet private_key from the path!"
    assert FetchAICrypto("./"), "Couldn't create a new entity for the given path!"


def test_get_address():
    """Test the get address."""
    fet_crypto = FetchAICrypto()
    assert (
        fet_crypto.get_address_from_public_key(fet_crypto.public_key)
        == fet_crypto.address
    ), "Get address must work"


def test_sign_message():
    """Test the signing process."""
    fet_crypto = FetchAICrypto()
    signature = fet_crypto.sign_message(message=b"HelloWorld")
    assert len(signature) > 1, "The len(signature) must be more than 0"


def test_get_address_from_public_key():
    """Test the address from public key."""
    fet_crypto = FetchAICrypto()
    address = FetchAICrypto().get_address_from_public_key(fet_crypto.public_key)
    assert str(address) == str(fet_crypto.address), "The address must be the same."


def test_recover_message():
    """Test the recover message"""
    fet_crypto = FetchAICrypto()
    with pytest.raises(NotImplementedError):
        fet_crypto.recover_message(message=b"hello", signature=b"signature")


def test_dump_positive():
    """Test dump."""
    account = FetchAICrypto(FETCHAI_PRIVATE_KEY_PATH)
    account.dump(MagicMock())


@pytest.mark.network
def test_get_balance():
    """Test the balance is zero for a new account."""
    fetch_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    fc = FetchAICrypto()
    balance = fetch_api.get_balance(fc.address)
    assert balance == 0, "New account has a positive balance."
    fc = FetchAICrypto(private_key_path=FETCHAI_PRIVATE_KEY_PATH)
    balance = fetch_api.get_balance(fc.address)
    # TODO
    # assert balance > 0, "Existing account has no balance."


@pytest.mark.network
def test_transfer():
    """Test transfer of wealth."""
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    fc1 = FetchAICrypto(private_key_path=FETCHAI_PRIVATE_KEY_PATH)
    fc2 = FetchAICrypto()
    amount = 40000
    fee = 30000
    tx_nonce = fetchai_api.generate_tx_nonce(fc2.address, fc1.address)
    tx_digest = fetchai_api.transfer(
        fc1, fc2.address, amount, fee, tx_nonce, chain_id=3
    )
    assert tx_digest is not None, "Failed to submit transfer!"
    # TODO:
    # not_settled = True
    # elapsed_time = 0
    # while not_settled and elapsed_time < 60:
    #     elapsed_time += 2
    #     time.sleep(2)
    #     is_settled = fetchai_api.is_transaction_settled(tx_digest)
    #     not_settled = not is_settled
    # assert is_settled, "Failed to complete tx!"
    # is_valid = fetchai_api.is_transaction_valid(
    #     tx_digest, fc2.address, fc1.address, tx_nonce, amount
    # )
    # assert is_valid, "Failed to settle tx correctly!"
