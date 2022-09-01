# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
from aea_ledger_cosmos import CosmosCrypto
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_ethereum.test_tools.constants import ETHEREUM_ADDRESS_ONE
from aea_ledger_fetchai import FetchAICrypto
from aea_ledger_fetchai.test_tools.constants import FETCHAI_ADDRESS_ONE

from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import AEAEnforceError

from tests.conftest import COSMOS_ADDRESS_ONE


logger = logging.getLogger(__name__)


def _raise_exception(*args, **kwargs):
    raise Exception("Message")


def test_initialisation():
    """Test the initialisation of the ledger APIs."""
    ledger_apis = LedgerApis
    assert ledger_apis.has_ledger(FetchAICrypto.identifier)
    assert type(LedgerApis.get_api(FetchAICrypto.identifier)).__name__ == "FetchAIApi"
    assert LedgerApis.has_ledger(EthereumCrypto.identifier)
    assert type(LedgerApis.get_api(EthereumCrypto.identifier)).__name__ == "EthereumApi"
    assert LedgerApis.has_ledger(CosmosCrypto.identifier)
    assert type(LedgerApis.get_api(CosmosCrypto.identifier)).__name__ == "CosmosApi"
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
        with mock.patch("aea_ledger_ethereum.EthereumApi.get_balance", return_value=10):
            balance = self.ledger_apis.get_balance(
                EthereumCrypto.identifier, ETHEREUM_ADDRESS_ONE
            )
            assert balance == 10

    def test_get_transfer_transaction(self):
        """Test the get_transfer_transaction."""
        with mock.patch(
            "aea_ledger_cosmos.CosmosApi.get_transfer_transaction",
            return_value="mock_transaction",
        ):
            tx = self.ledger_apis.get_transfer_transaction(
                identifier=CosmosCrypto.identifier,
                sender_address="sender_address",
                destination_address=COSMOS_ADDRESS_ONE,
                amount=10,
                tx_fee=10,
                tx_nonce="transaction nonce",
            )
            assert tx == "mock_transaction"

    def test_send_signed_transaction(self):
        """Test the send_signed_transaction."""
        with mock.patch(
            "aea_ledger_cosmos.CosmosApi.send_signed_transaction",
            return_value="mock_transaction_digest",
        ):
            tx_digest = self.ledger_apis.send_signed_transaction(
                identifier=CosmosCrypto.identifier,
                tx_signed="signed_transaction",
            )
            assert tx_digest == "mock_transaction_digest"

    def test_get_transaction_receipt(self):
        """Test the get_transaction_receipt."""
        with mock.patch(
            "aea_ledger_cosmos.CosmosApi.get_transaction_receipt",
            return_value="mock_transaction_receipt",
        ):
            tx_receipt = self.ledger_apis.get_transaction_receipt(
                identifier=CosmosCrypto.identifier,
                tx_digest="tx_digest",
            )
            assert tx_receipt == "mock_transaction_receipt"

    def test_get_transaction(self):
        """Test the get_transaction."""
        with mock.patch(
            "aea_ledger_cosmos.CosmosApi.get_transaction",
            return_value="mock_transaction",
        ):
            tx = self.ledger_apis.get_transaction(
                identifier=CosmosCrypto.identifier,
                tx_digest="tx_digest",
            )
            assert tx == "mock_transaction"

    def test_is_transaction_settled(self):
        """Test the is_transaction_settled."""
        with mock.patch(
            "aea_ledger_cosmos.CosmosApi.is_transaction_settled",
            return_value=True,
        ):
            is_settled = self.ledger_apis.is_transaction_settled(
                identifier=CosmosCrypto.identifier,
                tx_receipt="tx_receipt",
            )
            assert is_settled

    def test_is_transaction_valid(self):
        """Test the is_transaction_valid."""
        with mock.patch(
            "aea_ledger_cosmos.CosmosApi.is_transaction_valid",
            return_value=True,
        ):
            is_valid = self.ledger_apis.is_transaction_valid(
                identifier=CosmosCrypto.identifier,
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
        with mock.patch(
            "aea_ledger_cosmos.CosmosApi.recover_message",
            return_value=expected_addresses,
        ):
            addresses = self.ledger_apis.recover_message(
                identifier=CosmosCrypto.identifier,
                message="message",
                signature="signature",
            )
            assert addresses == expected_addresses

    def test_get_hash(self):
        """Test the get_hash."""
        expected_hash = "hash"
        with mock.patch(
            "aea_ledger_cosmos.CosmosApi.get_hash",
            return_value=expected_hash,
        ):
            hash_ = self.ledger_apis.get_hash(
                identifier=CosmosCrypto.identifier,
                message=b"message",
            )
            assert hash_ == expected_hash

    def test_get_contract_address(self):
        """Test the get_contract_address."""
        expected_address = "address"
        with mock.patch(
            "aea_ledger_cosmos.CosmosApi.get_contract_address",
            return_value=expected_address,
        ):
            address_ = self.ledger_apis.get_contract_address(
                identifier=CosmosCrypto.identifier,
                tx_receipt={},
            )
            assert address_ == expected_address

    def test_generate_tx_nonce_positive(self):
        """Test generate_tx_nonce positive result."""
        result = LedgerApis.generate_tx_nonce(
            CosmosCrypto.identifier, "seller", "client"
        )
        assert int(result, 16)


def test_is_valid_address():
    """Test LedgerApis.is_valid_address."""
    assert LedgerApis.is_valid_address(DEFAULT_LEDGER, ETHEREUM_ADDRESS_ONE)
    assert LedgerApis.is_valid_address(FetchAICrypto.identifier, FETCHAI_ADDRESS_ONE)
    assert LedgerApis.is_valid_address(CosmosCrypto.identifier, COSMOS_ADDRESS_ONE)
