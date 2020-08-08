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

"""This module contains tests for transaction."""

from aea.configurations.base import PublicId
from aea.helpers.transaction.base import (
    RawMessage,
    RawTransaction,
    SignedMessage,
    SignedTransaction,
    Terms,
)
from aea.protocols.signing.message import SigningMessage

from tests.conftest import COSMOS


class TestSigningMessage:
    """Test the signing message module."""

    @classmethod
    def setup_class(cls):
        """Setup class for test case."""
        cls.ledger_id = COSMOS
        cls.terms = Terms(
            ledger_id=cls.ledger_id,
            sender_address="address1",
            counterparty_address="address2",
            amount_by_currency_id={"FET": -2},
            quantities_by_good_id={"good_id": 10},
            is_sender_payable_tx_fee=True,
            nonce="transaction nonce",
        )
        cls.skill_callback_ids = (str(PublicId("author", "a_skill", "0.1.0")),)
        cls.skill_callback_info = {"some_string": "some_string"}

    def test_sign_transaction(self):
        """Test for an error for a sign transaction message."""
        tx_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            skill_callback_ids=self.skill_callback_ids,
            skill_callback_info=self.skill_callback_info,
            terms=self.terms,
            raw_transaction=RawTransaction(self.ledger_id, "transaction"),
        )
        assert tx_msg._is_consistent()
        encoded_tx_msg = tx_msg.encode()
        decoded_tx_msg = tx_msg.serializer.decode(encoded_tx_msg)
        assert tx_msg == decoded_tx_msg

    def test_sign_message(self):
        """Test for an error for a sign transaction message."""
        tx_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            skill_callback_ids=self.skill_callback_ids,
            skill_callback_info=self.skill_callback_info,
            terms=self.terms,
            raw_message=RawMessage(self.ledger_id, "message"),
        )
        assert tx_msg._is_consistent()
        encoded_tx_msg = tx_msg.encode()
        decoded_tx_msg = tx_msg.serializer.decode(encoded_tx_msg)
        assert tx_msg == decoded_tx_msg

    def test_signed_transaction(self):
        """Test for an error for a signed transaction."""
        tx_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGNED_TRANSACTION,
            message_id=2,
            target=1,
            skill_callback_ids=self.skill_callback_ids,
            skill_callback_info=self.skill_callback_info,
            signed_transaction=SignedTransaction(self.ledger_id, "signature"),
        )
        assert tx_msg._is_consistent()
        encoded_tx_msg = tx_msg.encode()
        decoded_tx_msg = tx_msg.serializer.decode(encoded_tx_msg)
        assert tx_msg == decoded_tx_msg

    def test_signed_message(self):
        """Test for an error for a signed message."""
        tx_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGNED_MESSAGE,
            message_id=2,
            target=1,
            skill_callback_ids=self.skill_callback_ids,
            skill_callback_info=self.skill_callback_info,
            signed_message=SignedMessage(self.ledger_id, "message"),
        )
        assert tx_msg._is_consistent()
        encoded_tx_msg = tx_msg.encode()
        decoded_tx_msg = tx_msg.serializer.decode(encoded_tx_msg)
        assert tx_msg == decoded_tx_msg

    def test_error_message(self):
        """Test for an error for an error message."""
        tx_msg = SigningMessage(
            performative=SigningMessage.Performative.ERROR,
            message_id=2,
            target=1,
            skill_callback_ids=self.skill_callback_ids,
            skill_callback_info=self.skill_callback_info,
            error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
        )
        assert tx_msg._is_consistent()
        encoded_tx_msg = tx_msg.encode()
        decoded_tx_msg = tx_msg.serializer.decode(encoded_tx_msg)
        assert tx_msg == decoded_tx_msg
        assert str(tx_msg.performative) == "error"
        assert len(tx_msg.valid_performatives) == 5


def test_serialization():
    """Test serialization."""
    skill_callback_ids = (str(PublicId("author", "a_skill", "0.1.0")),)
    skill_callback_info = {"some_string": "some_string"}
    tx_msg = SigningMessage(
        performative=SigningMessage.Performative.ERROR,
        message_id=2,
        target=1,
        skill_callback_ids=skill_callback_ids,
        skill_callback_info=skill_callback_info,
        error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
    )
    encoded_tx_bytes = tx_msg.serializer.encode(tx_msg)
    actual_tx_msg = tx_msg.serializer.decode(encoded_tx_bytes)
    assert tx_msg == actual_tx_msg
