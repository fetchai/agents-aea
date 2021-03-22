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
from typing import Type
from unittest.mock import patch

import pytest
from aea_ledger_cosmos import CosmosCrypto

from aea.common import Address
from aea.helpers.transaction.base import (
    RawMessage,
    RawTransaction,
    SignedMessage,
    SignedTransaction,
    Terms,
)
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

from packages.fetchai.protocols.signing.dialogues import (
    SigningDialogue as BaseSigningDialogue,
)
from packages.fetchai.protocols.signing.dialogues import (
    SigningDialogues as BaseSigningDialogues,
)
from packages.fetchai.protocols.signing.message import SigningMessage


class TestSigningMessage:
    """Test the signing message module."""

    @classmethod
    def setup_class(cls):
        """Setup class for test case."""
        cls.ledger_id = CosmosCrypto.identifier
        cls.terms = Terms(
            ledger_id=cls.ledger_id,
            sender_address="address1",
            counterparty_address="address2",
            amount_by_currency_id={"FET": -2},
            quantities_by_good_id={"good_id": 10},
            is_sender_payable_tx_fee=True,
            nonce="transaction nonce",
        )

    def test_sign_transaction(self):
        """Test for an error for a sign transaction message."""
        tx_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            terms=self.terms,
            raw_transaction=RawTransaction(self.ledger_id, {"tx": "transaction"}),
        )
        assert tx_msg._is_consistent()
        encoded_tx_msg = tx_msg.encode()
        decoded_tx_msg = tx_msg.serializer.decode(encoded_tx_msg)
        assert tx_msg == decoded_tx_msg

    def test_sign_message(self):
        """Test for an error for a sign transaction message."""
        tx_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            terms=self.terms,
            raw_message=RawMessage(self.ledger_id, b"message"),
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
            signed_transaction=SignedTransaction(self.ledger_id, {"sig": "signature"}),
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
            error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
        )
        assert tx_msg._is_consistent()
        encoded_tx_msg = tx_msg.encode()
        decoded_tx_msg = tx_msg.serializer.decode(encoded_tx_msg)
        assert tx_msg == decoded_tx_msg
        assert str(tx_msg.performative) == "error"
        assert len(tx_msg.valid_performatives) == 5


def test_consistency_check_negative():
    """Test the consistency check, negative case."""
    tx_msg = SigningMessage(performative=SigningMessage.Performative.SIGN_TRANSACTION,)
    assert not tx_msg._is_consistent()


def test_serialization_negative():
    """Test serialization when performative is not recognized."""
    tx_msg = SigningMessage(
        performative=SigningMessage.Performative.ERROR,
        message_id=2,
        target=1,
        error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
    )

    with patch.object(SigningMessage.Performative, "__eq__", return_value=False):
        with pytest.raises(
            ValueError, match=f"Performative not valid: {tx_msg.performative}"
        ):
            tx_msg.serializer.encode(tx_msg)

    encoded_tx_bytes = tx_msg.serializer.encode(tx_msg)
    with patch.object(SigningMessage.Performative, "__eq__", return_value=False):
        with pytest.raises(
            ValueError, match=f"Performative not valid: {tx_msg.performative}"
        ):
            tx_msg.serializer.decode(encoded_tx_bytes)


def test_dialogues():
    """Test intiaontiation of dialogues."""
    signing_dialogues = SigningDialogues("agent_addr")
    msg, dialogue = signing_dialogues.create(
        counterparty="abc",
        performative=SigningMessage.Performative.SIGN_TRANSACTION,
        terms=Terms(
            ledger_id="ledger_id",
            sender_address="address1",
            counterparty_address="address2",
            amount_by_currency_id={"FET": -2},
            quantities_by_good_id={"good_id": 10},
            is_sender_payable_tx_fee=True,
            nonce="transaction nonce",
        ),
        raw_transaction=RawTransaction("ledger_id", {"tx": "transaction"}),
    )
    assert dialogue is not None


class SigningDialogue(BaseSigningDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[SigningMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        BaseSigningDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class SigningDialogues(BaseSigningDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return SigningDialogue.Role.SKILL

        BaseSigningDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=SigningDialogue,
        )
