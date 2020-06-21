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
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.transaction.base import Terms


class TestTransaction:
    """Test the transaction module."""

    @classmethod
    def setup_class(cls):
        """Setup class for test case."""
        cls.terms = Terms(
            sender_addr="pk1",
            counterparty_addr="pk2",
            amount_by_currency_id={"FET": -2},
            is_sender_payable_tx_fee=True,
            quantities_by_good_id={"good_id": 10},
            nonce="transaction nonce",
        )
        cls.crypto_id = "fetchai"
        cls.skill_callback_ids = (PublicId("author", "a_skill", "0.1.0"),)
        cls.skill_callback_info = {"some_string": [1, 2]}

    def test_message_consistency(self):
        """Test for an error in consistency of a message."""
        tx_msg = TransactionMessage(
            performative=TransactionMessage.Performative.SIGN_TRANSACTION,
            skill_callback_ids=self.skill_callback_ids,
            skill_callback_info=self.skill_callback_info,
            terms=self.terms,
            crypto_id=self.crypto_id,
            transaction="transaction",
        )
        assert tx_msg._is_consistent()
        tx_msg = TransactionMessage(
            performative=TransactionMessage.Performative.SIGN_TRANSACTION,
            skill_callback_ids=self.skill_callback_ids,
            crypto_id=self.crypto_id,
            transaction="transaction",
        )
        assert tx_msg._is_consistent()
        tx_msg = TransactionMessage(
            performative=TransactionMessage.Performative.SIGN_MESSAGE,
            skill_callback_ids=self.skill_callback_ids,
            skill_callback_info=self.skill_callback_info,
            terms=self.terms,
            crypto_id=self.crypto_id,
            message=b"message",
        )
        assert tx_msg._is_consistent()
        tx_msg = TransactionMessage(
            performative=TransactionMessage.Performative.SIGN_MESSAGE,
            skill_callback_ids=self.skill_callback_ids,
            skill_callback_info=self.skill_callback_info,
            crypto_id=self.crypto_id,
            message=b"message",
        )
        assert tx_msg._is_consistent()
        tx_msg = TransactionMessage(
            performative=TransactionMessage.Performative.SIGNED_TRANSACTION,
            skill_callback_ids=self.skill_callback_ids,
            skill_callback_info=self.skill_callback_info,
            crypto_id=self.crypto_id,
            signed_transaction="signature",
        )
        assert tx_msg._is_consistent()
        tx_msg = TransactionMessage(
            performative=TransactionMessage.Performative.SIGNED_MESSAGE,
            skill_callback_ids=self.skill_callback_ids,
            skill_callback_info=self.skill_callback_info,
            crypto_id=self.crypto_id,
            signed_message="signature",
        )
        assert tx_msg._is_consistent()
        tx_msg = TransactionMessage(
            performative=TransactionMessage.Performative.ERROR,
            skill_callback_ids=self.skill_callback_ids,
            skill_callback_info=self.skill_callback_info,
            crypto_id=self.crypto_id,
            error_code=TransactionMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
        )
        assert tx_msg._is_consistent()
        assert str(tx_msg.performative) == "error"
        assert str(tx_msg.error_code) == "unsuccessful_message_signing"
        assert tx_msg.optional_callback_kwargs == {
            "skill_callback_info": tx_msg.skill_callback_info
        }

    def test_message_inconsistency(self):
        """Test for an error in consistency of a message."""

        tx_msg = TransactionMessage(
            performative=TransactionMessage.Performative.SIGN_TRANSACTION,
            skill_callback_ids=self.skill_callback_ids,
            crypto_id=self.crypto_id,
        )
        assert not tx_msg._is_consistent()
        tx_msg = TransactionMessage(
            performative=TransactionMessage.Performative.SIGN_MESSAGE,
            skill_callback_ids=self.skill_callback_ids,
            crypto_id=self.crypto_id,
        )
        assert not tx_msg._is_consistent()
