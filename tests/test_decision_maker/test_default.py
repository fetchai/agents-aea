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

"""This module contains tests for decision_maker."""
import os
from queue import Queue
from unittest import mock

import eth_account

import pytest

import aea
import aea.decision_maker.default
from aea.configurations.base import PublicId
from aea.crypto.ethereum import EthereumCrypto
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.decision_maker.default import DecisionMakerHandler
from aea.decision_maker.messages.state_update import StateUpdateMessage
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.transaction.base import Terms
from aea.identity.base import Identity

from ..conftest import CUR_PATH


class TestDecisionMaker:
    """Test the decision maker."""

    @classmethod
    def _patch_logger(cls):
        cls.patch_logger_warning = mock.patch.object(
            aea.decision_maker.default.logger, "warning"
        )
        cls.mocked_logger_warning = cls.patch_logger_warning.__enter__()

    @classmethod
    def _unpatch_logger(cls):
        cls.mocked_logger_warning.__exit__()

    @classmethod
    def setup_class(cls):
        """Initialise the decision maker."""
        cls._patch_logger()
        private_key_pem_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        eth_private_key_pem_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        cls.wallet = Wallet(
            {
                FetchAICrypto.identifier: private_key_pem_path,
                EthereumCrypto.identifier: eth_private_key_pem_path,
            }
        )
        cls.agent_name = "test"
        cls.identity = Identity(
            cls.agent_name,
            addresses=cls.wallet.addresses,
            default_address_key=FetchAICrypto.identifier,
        )
        cls.decision_maker_handler = DecisionMakerHandler(
            identity=cls.identity, wallet=cls.wallet
        )
        cls.decision_maker = DecisionMaker(cls.decision_maker_handler)

        cls.tx_sender_addr = "agent_1"
        cls.tx_counterparty_addr = "pk"
        cls.info = {"some_info_key": "some_info_value"}
        cls.ledger_id = "fetchai"

        cls.decision_maker.start()

    def test_properties(self):
        """Test the properties of the decision maker."""
        assert isinstance(self.decision_maker.message_in_queue, Queue)
        assert isinstance(self.decision_maker.message_out_queue, Queue)

    def test_decision_maker_handle_state_update_initialize_and_apply(self):
        """Test the handle method for a stateUpdate message with Initialize and Apply performative."""
        good_holdings = {"good_id": 2}
        currency_holdings = {"FET": 100}
        utility_params = {"good_id": 20.0}
        exchange_params = {"FET": 10.0}
        currency_deltas = {"FET": -10}
        good_deltas = {"good_id": 1}

        tx_fee = 1
        state_update_message = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.INITIALIZE,
            amount_by_currency_id=currency_holdings,
            quantities_by_good_id=good_holdings,
            exchange_params_by_currency_id=exchange_params,
            utility_params_by_good_id=utility_params,
            tx_fee=tx_fee,
        )
        self.decision_maker.handle(state_update_message)
        assert (
            self.decision_maker_handler.context.ownership_state.amount_by_currency_id
            is not None
        )
        assert (
            self.decision_maker_handler.context.ownership_state.quantities_by_good_id
            is not None
        )
        assert (
            self.decision_maker_handler.context.preferences.exchange_params_by_currency_id
            is not None
        )
        assert (
            self.decision_maker_handler.context.preferences.utility_params_by_good_id
            is not None
        )

        state_update_message = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.APPLY,
            amount_by_currency_id=currency_deltas,
            quantities_by_good_id=good_deltas,
        )
        self.decision_maker.handle(state_update_message)
        expected_amount_by_currency_id = {
            key: currency_holdings.get(key, 0) + currency_deltas.get(key, 0)
            for key in set(currency_holdings) | set(currency_deltas)
        }
        expected_quantities_by_good_id = {
            key: good_holdings.get(key, 0) + good_deltas.get(key, 0)
            for key in set(good_holdings) | set(good_deltas)
        }
        assert (
            self.decision_maker_handler.context.ownership_state.amount_by_currency_id
            == expected_amount_by_currency_id
        ), "The amount_by_currency_id must be equal with the expected amount."
        assert (
            self.decision_maker_handler.context.ownership_state.quantities_by_good_id
            == expected_quantities_by_good_id
        )

    def test_decision_maker_execute_w_wrong_input(self):
        """Test the execute method with wrong input."""
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.put_nowait("wrong input")
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.put("wrong input")

    def test_decision_maker_queue_access_not_permitted(self):
        """Test the in queue of the decision maker can not be accessed."""
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.get()
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.get_nowait()
        with pytest.raises(ValueError):
            self.decision_maker.message_in_queue.protected_get(
                access_code="some_invalid_code"
            )

    def test_handle_tx_sigining_fetchai(self):
        """Test tx signing for fetchai."""
        tx = {}
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.SIGN_TRANSACTION,
            skill_callback_ids=(PublicId("author", "a_skill", "0.1.0"),),
            crypto_id="fetchai",
            transaction=tx,
        )
        with pytest.raises(NotImplementedError):
            self.decision_maker_handler.handle(tx_message)

    def test_handle_tx_sigining_ethereum(self):
        """Test tx signing for ethereum."""
        tx = {"gasPrice": 30, "nonce": 1, "gas": 20000}
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.SIGN_TRANSACTION,
            skill_callback_ids=(PublicId("author", "a_skill", "0.1.0"),),
            crypto_id="ethereum",
            transaction=tx,
        )
        self.decision_maker.message_in_queue.put_nowait(tx_message)
        tx_message_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert (
            tx_message_response.performative
            == TransactionMessage.Performative.SIGNED_TRANSACTION
        )
        assert tx_message_response.skill_callback_ids == tx_message.skill_callback_ids
        assert (
            type(tx_message_response.signed_transaction)
            == eth_account.datastructures.AttributeDict
        )

    def test_handle_tx_signing_unknown(self):
        """Test tx signing for unknown."""
        tx = {}
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.SIGN_TRANSACTION,
            skill_callback_ids=(PublicId("author", "a_skill", "0.1.0"),),
            terms=Terms(
                sender_addr="pk1",
                counterparty_addr="pk2",
                amount_by_currency_id={"FET": -1},
                is_sender_payable_tx_fee=True,
                quantities_by_good_id={"good_id": 10},
                nonce="transaction nonce",
            ),
            crypto_id="unknown",
            transaction=tx,
        )
        self.decision_maker.message_in_queue.put_nowait(tx_message)
        tx_message_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert tx_message_response.performative == TransactionMessage.Performative.ERROR
        assert tx_message_response.skill_callback_ids == tx_message.skill_callback_ids
        assert (
            tx_message_response.error_code
            == TransactionMessage.ErrorCode.UNSUCCESSFUL_TRANSACTION_SIGNING
        )

    def test_handle_message_signing_fetchai(self):
        """Test message signing for fetchai."""
        message = b"0x11f3f9487724404e3a1fb7252a322656b90ba0455a2ca5fcdcbe6eeee5f8126d"
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.SIGN_MESSAGE,
            skill_callback_ids=(PublicId("author", "a_skill", "0.1.0"),),
            crypto_id="fetchai",
            message=message,
        )
        self.decision_maker.message_in_queue.put_nowait(tx_message)
        tx_message_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert (
            tx_message_response.performative
            == TransactionMessage.Performative.SIGNED_MESSAGE
        )
        assert tx_message_response.skill_callback_ids == tx_message.skill_callback_ids
        assert type(tx_message_response.signed_message) == str

    def test_handle_message_signing_ethereum(self):
        """Test message signing for ethereum."""
        message = b"0x11f3f9487724404e3a1fb7252a322656b90ba0455a2ca5fcdcbe6eeee5f8126d"
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.SIGN_MESSAGE,
            skill_callback_ids=(PublicId("author", "a_skill", "0.1.0"),),
            crypto_id="ethereum",
            message=message,
        )
        self.decision_maker.message_in_queue.put_nowait(tx_message)
        tx_message_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert (
            tx_message_response.performative
            == TransactionMessage.Performative.SIGNED_MESSAGE
        )
        assert tx_message_response.skill_callback_ids == tx_message.skill_callback_ids
        assert type(tx_message_response.signed_message) == str

    def test_handle_message_signing_ethereum_deprecated(self):
        """Test message signing for ethereum deprecated."""
        message = b"0x11f3f9487724404e3a1fb7252a3226"
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.SIGN_MESSAGE,
            skill_callback_ids=(PublicId("author", "a_skill", "0.1.0"),),
            crypto_id="ethereum",
            is_deprecated_signing_mode=True,
            message=message,
        )
        self.decision_maker.message_in_queue.put_nowait(tx_message)
        tx_message_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert (
            tx_message_response.performative
            == TransactionMessage.Performative.SIGNED_MESSAGE
        )
        assert tx_message_response.skill_callback_ids == tx_message.skill_callback_ids
        assert type(tx_message_response.signed_message) == str

    def test_handle_message_signing_unknown(self):
        """Test message signing for unknown."""
        message = b"0x11f3f9487724404e3a1fb7252a322656b90ba0455a2ca5fcdcbe6eeee5f8126d"
        tx_message = TransactionMessage(
            performative=TransactionMessage.Performative.SIGN_MESSAGE,
            skill_callback_ids=(PublicId("author", "a_skill", "0.1.0"),),
            crypto_id="unknown",
            message=message,
        )
        self.decision_maker.message_in_queue.put_nowait(tx_message)
        tx_message_response = self.decision_maker.message_out_queue.get(timeout=2)
        assert tx_message_response.performative == TransactionMessage.Performative.ERROR
        assert tx_message_response.skill_callback_ids == tx_message.skill_callback_ids
        assert (
            tx_message_response.error_code
            == TransactionMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING
        )

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        cls._unpatch_logger()
        cls.decision_maker.stop()
