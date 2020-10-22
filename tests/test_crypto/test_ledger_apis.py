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

"""This module contains the tests for the crypto/helpers module."""

import logging
from unittest import mock

import pytest

from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.cosmos import CosmosApi, CosmosCrypto
from aea.crypto.ethereum import EthereumApi, EthereumCrypto
from aea.crypto.fetchai import FetchAIApi
from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import AEAEnforceError

from tests.conftest import (
    COSMOS,
    COSMOS_ADDRESS_ONE,
    ETHEREUM_ADDRESS_ONE,
    FETCHAI_ADDRESS_ONE,
)


logger = logging.getLogger(__name__)


def _raise_exception(*args, **kwargs):
    raise Exception("Message")


def test_initialisation():
    """Test the initialisation of the ledger APIs."""
    ledger_apis = LedgerApis
    assert ledger_apis.has_ledger(FetchAIApi.identifier)
    assert type(LedgerApis.get_api(FetchAIApi.identifier)) == FetchAIApi
    assert LedgerApis.has_ledger(EthereumApi.identifier)
    assert type(LedgerApis.get_api(EthereumApi.identifier)) == EthereumApi
    assert LedgerApis.has_ledger(CosmosApi.identifier)
    assert type(LedgerApis.get_api(CosmosApi.identifier)) == CosmosApi
    with pytest.raises(AEAEnforceError):
        ledger_apis.get_api("UNKNOWN")


class TestLedgerApis:
    """Test the ledger_apis module."""

    @classmethod
    def setup_class(cls):
        """Setup the test case."""
        cls.ledger_apis = LedgerApis

    def test_get_balance(self):
        """Test the get_balance."""
        with mock.patch.object(EthereumApi, "get_balance", return_value=10):
            balance = self.ledger_apis.get_balance(
                EthereumApi.identifier, ETHEREUM_ADDRESS_ONE
            )
            assert balance == 10

    def test_get_transfer_transaction(self):
        """Test the get_transfer_transaction."""
        with mock.patch.object(
            CosmosApi, "get_transfer_transaction", return_value="mock_transaction",
        ):
            tx = self.ledger_apis.get_transfer_transaction(
                identifier=COSMOS,
                sender_address="sender_address",
                destination_address=COSMOS_ADDRESS_ONE,
                amount=10,
                tx_fee=10,
                tx_nonce="transaction nonce",
            )
            assert tx == "mock_transaction"

    def test_send_signed_transaction(self):
        """Test the send_signed_transaction."""
        with mock.patch.object(
            CosmosApi,
            "send_signed_transaction",
            return_value="mock_transaction_digest",
        ):
            tx_digest = self.ledger_apis.send_signed_transaction(
                identifier=COSMOS, tx_signed="signed_transaction",
            )
            assert tx_digest == "mock_transaction_digest"

    def test_get_transaction_receipt(self):
        """Test the get_transaction_receipt."""
        with mock.patch.object(
            CosmosApi,
            "get_transaction_receipt",
            return_value="mock_transaction_receipt",
        ):
            tx_receipt = self.ledger_apis.get_transaction_receipt(
                identifier=COSMOS, tx_digest="tx_digest",
            )
            assert tx_receipt == "mock_transaction_receipt"

    def test_get_transaction(self):
        """Test the get_transaction."""
        with mock.patch.object(
            CosmosApi, "get_transaction", return_value="mock_transaction",
        ):
            tx = self.ledger_apis.get_transaction(
                identifier=COSMOS, tx_digest="tx_digest",
            )
            assert tx == "mock_transaction"

    def test_is_transaction_settled(self):
        """Test the is_transaction_settled."""
        with mock.patch.object(
            CosmosApi, "is_transaction_settled", return_value=True,
        ):
            is_settled = self.ledger_apis.is_transaction_settled(
                identifier=COSMOS, tx_receipt="tx_receipt",
            )
            assert is_settled

    def test_is_transaction_valid(self):
        """Test the is_transaction_valid."""
        with mock.patch.object(
            CosmosApi, "is_transaction_valid", return_value=True,
        ):
            is_valid = self.ledger_apis.is_transaction_valid(
                identifier=COSMOS,
                tx="tx",
                seller="seller",
                client="client",
                tx_nonce="tx_nonce",
                amount=10,
            )
            assert is_valid

    def test_recover_message(self):
        """Test the is_transaction_valid."""
        expected_addresses = ("address_1", "address_2")
        with mock.patch.object(
            CosmosApi, "recover_message", return_value=expected_addresses,
        ):
            addresses = self.ledger_apis.recover_message(
                identifier=COSMOS, message="message", signature="signature",
            )
            assert addresses == expected_addresses

    def test_get_hash(self):
        """Test the is_transaction_valid."""
        expected_hash = "hash"
        with mock.patch.object(
            CosmosApi, "get_hash", return_value=expected_hash,
        ):
            hash_ = self.ledger_apis.get_hash(identifier=COSMOS, message=b"message",)
            assert hash_ == expected_hash

    def test_generate_tx_nonce_positive(self):
        """Test generate_tx_nonce positive result."""
        result = LedgerApis.generate_tx_nonce(CosmosApi.identifier, "seller", "client")
        assert int(result, 16)


def test_is_valid_address():
    """Test LedgerApis.is_valid_address."""
    assert LedgerApis.is_valid_address(DEFAULT_LEDGER, FETCHAI_ADDRESS_ONE)
    assert LedgerApis.is_valid_address(EthereumCrypto.identifier, ETHEREUM_ADDRESS_ONE)
    assert LedgerApis.is_valid_address(CosmosCrypto.identifier, COSMOS_ADDRESS_ONE)
