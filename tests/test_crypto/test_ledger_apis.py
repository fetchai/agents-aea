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

from aea.crypto.cosmos import CosmosApi
from aea.crypto.ethereum import EthereumApi
from aea.crypto.fetchai import FetchAIApi
from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import AEAException

from tests.conftest import (
    COSMOS_TESTNET_CONFIG,
    ETHEREUM_ADDRESS_ONE,
    ETHEREUM_TESTNET_CONFIG,
    FETCHAI,
    FETCHAI_ADDRESS_ONE,
    FETCHAI_TESTNET_CONFIG,
)

logger = logging.getLogger(__name__)


def _raise_exception(*args, **kwargs):
    raise Exception("Message")


def test_initialisation():
    """Test the initialisation of the ledger APIs."""
    ledger_apis = LedgerApis(
        {
            EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
            FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            CosmosApi.identifier: COSMOS_TESTNET_CONFIG,
        },
        FetchAIApi.identifier,
    )
    assert ledger_apis.configs.get(EthereumApi.identifier) == ETHEREUM_TESTNET_CONFIG
    assert ledger_apis.has_ledger(FetchAIApi.identifier)
    assert type(ledger_apis.get_api(FetchAIApi.identifier)) == FetchAIApi
    assert ledger_apis.has_ledger(EthereumApi.identifier)
    assert type(ledger_apis.get_api(EthereumApi.identifier)) == EthereumApi
    assert ledger_apis.has_ledger(CosmosApi.identifier)
    assert type(ledger_apis.get_api(CosmosApi.identifier)) == CosmosApi
    unknown_config = {"UnknownPath": 8080}
    with pytest.raises(AEAException):
        LedgerApis({"UNKNOWN": unknown_config}, FetchAIApi.identifier)


class TestLedgerApis:
    """Test the ledger_apis module."""

    @classmethod
    def setup_class(cls):
        """Setup the test case."""
        cls.ledger_apis = LedgerApis(
            {
                EthereumApi.identifier: ETHEREUM_TESTNET_CONFIG,
                FetchAIApi.identifier: FETCHAI_TESTNET_CONFIG,
            },
            FetchAIApi.identifier,
        )

    def test_get_balance(self):
        """Test the get_balance."""
        api = self.ledger_apis.apis[EthereumApi.identifier]
        with mock.patch.object(api.api.eth, "getBalance", return_value=10):
            balance = self.ledger_apis.get_balance(
                EthereumApi.identifier, ETHEREUM_ADDRESS_ONE
            )
            assert balance == 10

        with mock.patch.object(
            api.api.eth, "getBalance", return_value=0, side_effect=Exception
        ):
            balance = self.ledger_apis.get_balance(
                EthereumApi.identifier, FETCHAI_ADDRESS_ONE
            )
            assert balance is None, "This must be None since the address is wrong"

    def test_get_transfer_transaction(self):
        """Test the get_transfer_transaction."""
        with mock.patch.object(
            self.ledger_apis.apis.get(FetchAIApi.identifier),
            "get_transfer_transaction",
            return_value="mock_transaction",
        ):
            tx = self.ledger_apis.get_transfer_transaction(
                identifier=FETCHAI,
                sender_address="sender_address",
                destination_address=FETCHAI_ADDRESS_ONE,
                amount=10,
                tx_fee=10,
                tx_nonce="transaction nonce",
            )
            assert tx == "mock_transaction"

    def test_send_signed_transaction(self):
        """Test the send_signed_transaction."""
        with mock.patch.object(
            self.ledger_apis.apis.get(FetchAIApi.identifier),
            "send_signed_transaction",
            return_value="mock_transaction_digest",
        ):
            tx_digest = self.ledger_apis.send_signed_transaction(
                identifier=FETCHAI, tx_signed="signed_transaction",
            )
            assert tx_digest == "mock_transaction_digest"

    def test_get_transaction_receipt(self):
        """Test the get_transaction_receipt."""
        with mock.patch.object(
            self.ledger_apis.apis.get(FetchAIApi.identifier),
            "get_transaction_receipt",
            return_value="mock_transaction_receipt",
        ):
            tx_receipt = self.ledger_apis.get_transaction_receipt(
                identifier=FETCHAI, tx_digest="tx_digest",
            )
            assert tx_receipt == "mock_transaction_receipt"

    def test_get_transaction(self):
        """Test the get_transaction."""
        with mock.patch.object(
            self.ledger_apis.apis.get(FetchAIApi.identifier),
            "get_transaction",
            return_value="mock_transaction",
        ):
            tx = self.ledger_apis.get_transaction(
                identifier=FETCHAI, tx_digest="tx_digest",
            )
            assert tx == "mock_transaction"

    def test_is_transaction_settled(self):
        """Test the is_transaction_settled."""
        with mock.patch.object(
            FetchAIApi, "is_transaction_settled", return_value=True,
        ):
            is_settled = self.ledger_apis.is_transaction_settled(
                identifier=FETCHAI, tx_receipt="tx_receipt",
            )
            assert is_settled

    def test_is_transaction_valid(self):
        """Test the is_transaction_valid."""
        with mock.patch.object(
            FetchAIApi, "is_transaction_valid", return_value=True,
        ):
            is_valid = self.ledger_apis.is_transaction_valid(
                identifier=FETCHAI,
                tx="tx",
                seller="seller",
                client="client",
                tx_nonce="tx_nonce",
                amount=10,
            )
            assert is_valid

    def test_generate_tx_nonce_positive(self):
        """Test generate_tx_nonce positive result."""
        result = self.ledger_apis.generate_tx_nonce(
            FetchAIApi.identifier, "seller", "client"
        )
        assert int(result, 16)

    def test_has_default_ledger_positive(self):
        """Test has_default_ledger init positive result."""
        assert self.ledger_apis.has_default_ledger
