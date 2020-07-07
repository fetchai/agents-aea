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
import logging
import time
from unittest.mock import MagicMock

from fetchai.ledger.transaction import Transaction

import pytest

from aea.crypto.fetchai import FetchAIApi, FetchAICrypto, FetchAIFaucetApi

from tests.conftest import (
    FETCHAI_PRIVATE_KEY_PATH,
    FETCHAI_TESTNET_CONFIG,
    MAX_FLAKY_RERUNS,
)


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


def test_sign_and_recover_message():
    """Test the signing and the recovery of a message."""
    account = FetchAICrypto(FETCHAI_PRIVATE_KEY_PATH)
    sign_bytes = account.sign_message(message=b"hello")
    assert len(sign_bytes) > 0, "The len(signature) must not be 0"
    recovered_addresses = FetchAIApi.recover_message(
        message=b"hello", signature=sign_bytes
    )
    assert (
        account.address in recovered_addresses
    ), "Failed to recover the correct address."


def test_get_address_from_public_key():
    """Test the address from public key."""
    fet_crypto = FetchAICrypto()
    address = FetchAIApi.get_address_from_public_key(fet_crypto.public_key)
    assert address == fet_crypto.address, "The address must be the same."


def test_dump_positive():
    """Test dump."""
    account = FetchAICrypto(FETCHAI_PRIVATE_KEY_PATH)
    account.dump(MagicMock())


def test_api_creation():
    """Test api instantiation."""
    assert FetchAIApi(**FETCHAI_TESTNET_CONFIG), "Failed to initialise the api"


def test_api_none():
    """Test the "api" of the cryptoApi is none."""
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    assert fetchai_api.api is not None, "The api property is None."


def test_generate_nonce():
    """Test generate nonce."""
    nonce = FetchAIApi.generate_tx_nonce(
        seller="some_seller_addr", client="some_buyer_addr"
    )
    assert len(nonce) > 0 and int(
        nonce, 16
    ), "The len(nonce) must not be 0 and must be hex"


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_construct_sign_and_submit_transfer_transaction():
    """Test the construction, signing and submitting of a transfer transaction."""
    account = FetchAICrypto(FETCHAI_PRIVATE_KEY_PATH)
    fc2 = FetchAICrypto()
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)

    amount = 10000
    transfer_transaction = fetchai_api.get_transfer_transaction(
        sender_address=account.address,
        destination_address=fc2.address,
        amount=amount,
        tx_fee=1000,
        tx_nonce="",
    )
    assert isinstance(
        transfer_transaction, Transaction
    ), "Incorrect transfer_transaction constructed."

    signed_transaction = account.sign_transaction(transfer_transaction)
    assert (
        isinstance(signed_transaction, Transaction)
        and len(signed_transaction.signatures) == 1
    ), "Incorrect signed_transaction constructed."

    transaction_digest = fetchai_api.send_signed_transaction(signed_transaction)
    assert transaction_digest is not None, "Failed to submit transfer transaction!"

    not_settled = True
    elapsed_time = 0
    while not_settled and elapsed_time < 20:
        elapsed_time += 1
        time.sleep(2)
        transaction_receipt = fetchai_api.get_transaction_receipt(transaction_digest)
        if transaction_receipt is None:
            continue
        is_settled = fetchai_api.is_transaction_settled(transaction_receipt)
        if is_settled is None:
            continue
        not_settled = not is_settled
    assert transaction_receipt is not None, "Failed to retrieve transaction receipt."
    assert is_settled, "Failed to verify tx!"

    tx = fetchai_api.get_transaction(transaction_digest)
    assert tx != transaction_receipt, "Should be same!"
    is_valid = fetchai_api.is_transaction_valid(
        tx, fc2.address, account.address, "", amount
    )
    assert is_valid, "Failed to settle tx correctly!"


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_balance():
    """Test the balance is zero for a new account."""
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    fc = FetchAICrypto()
    balance = fetchai_api.get_balance(fc.address)
    assert balance == 0, "New account has a positive balance."
    fc = FetchAICrypto(private_key_path=FETCHAI_PRIVATE_KEY_PATH)
    balance = fetchai_api.get_balance(fc.address)
    assert balance > 0, "Existing account has no balance."


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_wealth_positive(caplog):
    """Test the balance is zero for a new account."""
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.fetchai"):
        fetchai_faucet_api = FetchAIFaucetApi()
        fc = FetchAICrypto()
        fetchai_faucet_api.get_wealth(fc.address)
        assert (
            "Message: Transfer pending" in caplog.text
        ), f"Cannot find message in output: {caplog.text}"
