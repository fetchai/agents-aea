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
from unittest import mock
from unittest.mock import MagicMock, call

import pytest

from aea.crypto.fetchai import FetchAIApi, FetchAICrypto, FetchAIFaucetApi

from tests.conftest import (
    FETCHAI_PRIVATE_KEY_PATH,
    FETCHAI_TESTNET_CONFIG,
    # MAX_FLAKY_RERUNS,
)


class MockRequestsResponse:
    def __init__(self, data, status_code=None):
        self._data = data
        self._status_code = status_code or 200

    @property
    def status_code(self):
        return 200

    def json(self):
        return self._data


def test_creation():
    """Test the creation of the crypto_objects."""
    assert FetchAICrypto(), "Did not manage to initialise the crypto module"
    assert FetchAICrypto(
        FETCHAI_PRIVATE_KEY_PATH
    ), "Did not manage to load the cosmos private key"


def test_initialization():
    """Test the initialisation of the variables."""
    account = FetchAICrypto()
    assert account.entity is not None, "The property must return the account."
    assert (
        account.address is not None
    ), "After creation the display address must not be None"
    assert account.address.startswith("fetch")
    assert (
        account.public_key is not None
    ), "After creation the public key must no be None"


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


def test_get_hash():
    """Test the get hash functionality."""
    expected_hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    hash_ = FetchAIApi.get_hash(message=b"hello")
    assert expected_hash == hash_


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
    assert fetchai_api.api is None, "The api property is not None."


def test_generate_nonce():
    """Test generate nonce."""
    nonce = FetchAIApi.generate_tx_nonce(
        seller="some_seller_addr", client="some_buyer_addr"
    )
    assert len(nonce) > 0 and int(
        nonce, 16
    ), "The len(nonce) must not be 0 and must be hex"


def test_get_address_from_public_key():
    """Test the address from public key."""
    fet_crypto = FetchAICrypto()
    address = FetchAIApi.get_address_from_public_key(fet_crypto.public_key)
    assert address == fet_crypto.address, "The address must be the same."


# @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_construct_sign_and_submit_transfer_transaction():
    """Test the construction, signing and submitting of a transfer transaction."""
    account = FetchAICrypto()
    balance = get_wealth(account.address)
    assert balance > 0, "Failed to fund account."
    fc2 = FetchAICrypto()
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)

    amount = 10000
    assert amount < balance, "Not enough funds."
    transfer_transaction = fetchai_api.get_transfer_transaction(
        sender_address=account.address,
        destination_address=fc2.address,
        amount=amount,
        tx_fee=1000,
        tx_nonce="something",
    )
    assert (
        isinstance(transfer_transaction, dict) and len(transfer_transaction) == 6
    ), "Incorrect transfer_transaction constructed."

    signed_transaction = account.sign_transaction(transfer_transaction)
    assert (
        isinstance(signed_transaction, dict)
        and len(signed_transaction["tx"]) == 4
        and isinstance(signed_transaction["tx"]["signatures"], list)
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
        not_settled = not is_settled
    assert transaction_receipt is not None, "Failed to retrieve transaction receipt."
    assert is_settled, "Failed to verify tx!"

    tx = fetchai_api.get_transaction(transaction_digest)
    is_valid = fetchai_api.is_transaction_valid(
        tx, fc2.address, account.address, "", amount
    )
    assert is_valid, "Failed to settle tx correctly!"
    assert tx == transaction_receipt, "Should be same!"


# @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_balance():
    """Test the balance is zero for a new account."""
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    fc = FetchAICrypto()
    balance = fetchai_api.get_balance(fc.address)
    assert balance == 0, "New account has a positive balance."
    balance = get_wealth(fc.address)
    assert balance > 0, "Existing account has no balance."


def get_wealth(address: str):
    """Get wealth for test."""
    fetchai_api = FetchAIApi(**FETCHAI_TESTNET_CONFIG)
    FetchAIFaucetApi().get_wealth(address)
    balance = 0
    timeout = 0
    while timeout < 40 and balance == 0:
        time.sleep(1)
        timeout += 1
        _balance = fetchai_api.get_balance(address)
        balance = _balance if _balance is not None else 0
    return balance


# @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_wealth_positive(caplog):
    """Test the balance is zero for a new account."""
    with caplog.at_level(logging.DEBUG, logger="aea.crypto.fetchai"):
        fetchai_faucet_api = FetchAIFaucetApi()
        fc = FetchAICrypto()
        fetchai_faucet_api.get_wealth(fc.address)
        assert "Wealth generated" in caplog.text


@pytest.mark.ledger
@mock.patch("requests.get")
@mock.patch("requests.post")
def test_successful_faucet_operation(mock_post, mock_get):
    address = "a normal cosmos address would be here"
    mock_post.return_value = MockRequestsResponse({"uid": "a-uuid-v4-would-be-here"})

    mock_get.return_value = MockRequestsResponse(
        {
            "uid": "a-uuid-v4-would-be-here",
            "txDigest": "0x transaction hash would be here",
            "status": "completed",
            "statusCode": FetchAIFaucetApi.FAUCET_STATUS_COMPLETED,
        }
    )

    faucet = FetchAIFaucetApi()
    faucet.get_wealth(address)

    mock_post.assert_has_calls(
        [
            call(
                url=f"{FetchAIFaucetApi.testnet_faucet_url}/claim/requests",
                data={"Address": address},
            )
        ]
    )
    mock_get.assert_has_calls(
        [
            call(
                f"{FetchAIFaucetApi.testnet_faucet_url}/claim/requests/a-uuid-v4-would-be-here"
            )
        ]
    )


@pytest.mark.ledger
@mock.patch("requests.get")
@mock.patch("requests.post")
def test_successful_realistic_faucet_operation(mock_post, mock_get):
    address = "a normal cosmos address would be here"
    mock_post.return_value = MockRequestsResponse({"uid": "a-uuid-v4-would-be-here"})

    mock_get.side_effect = [
        MockRequestsResponse(
            {
                "uid": "a-uuid-v4-would-be-here",
                "txDigest": None,
                "status": "pending",
                "statusCode": FetchAIFaucetApi.FAUCET_STATUS_PENDING,
            }
        ),
        MockRequestsResponse(
            {
                "uid": "a-uuid-v4-would-be-here",
                "txDigest": None,
                "status": "processing",
                "statusCode": FetchAIFaucetApi.FAUCET_STATUS_PROCESSING,
            }
        ),
        MockRequestsResponse(
            {
                "uid": "a-uuid-v4-would-be-here",
                "txDigest": "0x transaction hash would be here",
                "status": "completed",
                "statusCode": FetchAIFaucetApi.FAUCET_STATUS_COMPLETED,
            }
        ),
    ]

    faucet = FetchAIFaucetApi(poll_interval=0)
    faucet.get_wealth(address)

    mock_post.assert_has_calls(
        [
            call(
                url=f"{FetchAIFaucetApi.testnet_faucet_url}/claim/requests",
                data={"Address": address},
            )
        ]
    )
    mock_get.assert_has_calls(
        [
            call(
                f"{FetchAIFaucetApi.testnet_faucet_url}/claim/requests/a-uuid-v4-would-be-here"
            ),
            call(
                f"{FetchAIFaucetApi.testnet_faucet_url}/claim/requests/a-uuid-v4-would-be-here"
            ),
            call(
                f"{FetchAIFaucetApi.testnet_faucet_url}/claim/requests/a-uuid-v4-would-be-here"
            ),
        ]
    )
