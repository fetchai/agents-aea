# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

"""This module contains the tests of the messages module."""
# pylint: skip-file

from typing import Type
from unittest import mock

import pytest

from aea.common import Address
from aea.exceptions import AEAEnforceError
from aea.helpers.transaction.base import State
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

from packages.fetchai.protocols.ledger_api import message
from packages.fetchai.protocols.ledger_api.custom_types import Kwargs
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogue,
    LedgerApiDialogues,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.ledger_api.message import (
    _default_logger as ledger_api_message_logger,
)


def test_get_balance_serialization():
    """Test the serialization for 'get_balance' speech-act works."""
    msg = LedgerApiMessage(
        performative=LedgerApiMessage.Performative.GET_BALANCE,
        ledger_id="some_ledger_id",
        address="some_address",
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = LedgerApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_get_state_serialization():
    """Test the serialization for 'get_state' speech-act works."""

    args = ("arg1", "arg2")
    kwargs = Kwargs({"key": "value"})

    assert str(kwargs) == "Kwargs: body={'key': 'value'}"

    msg = LedgerApiMessage(
        performative=LedgerApiMessage.Performative.GET_STATE,
        ledger_id="some_ledger_id",
        callable="some_function",
        args=args,
        kwargs=kwargs,
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = LedgerApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_get_raw_transaction_serialization():
    """Test the serialization for 'get_raw_transaction' speech-act works."""
    terms_arg = LedgerApiMessage.Terms(
        ledger_id="some_ledger_id",
        sender_address="some_sender_address",
        counterparty_address="some_counterparty_address",
        amount_by_currency_id={"currency_id_1": 1},
        quantities_by_good_id={"good_id_1": -1, "good_id_2": -2},
        nonce="some_nonce",
        is_sender_payable_tx_fee=False,
        fee_by_currency_id={"currency_id_1": 1},
        is_strict=True,
    )
    msg = LedgerApiMessage(
        message_id=2,
        target=1,
        performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
        terms=terms_arg,
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = LedgerApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_send_signed_transaction_serialization():
    """Test the serialization for 'send_signed_transaction' speech-act works."""
    msg = LedgerApiMessage(
        message_id=2,
        target=1,
        performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
        signed_transaction=LedgerApiMessage.SignedTransaction(
            "some_ledger_id", {"body": "some_body"}
        ),
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = LedgerApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_get_transaction_receipt_serialization():
    """Test the serialization for 'get_transaction_receipt' speech-act works."""
    msg = LedgerApiMessage(
        message_id=2,
        target=1,
        performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
        transaction_digest=LedgerApiMessage.TransactionDigest(
            "some_ledger_id", "some_body"
        ),
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = LedgerApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_balance_serialization():
    """Test the serialization for 'balance' speech-act works."""
    msg = LedgerApiMessage(
        message_id=2,
        target=1,
        performative=LedgerApiMessage.Performative.BALANCE,
        ledger_id="some_ledger_id",
        balance=125,
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = LedgerApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_state_serialization():
    """Test the serialization for 'state' speech-act works."""

    ledger_id = "some_ledger_id"
    state = State(ledger_id, {"key": "some_state"})

    msg = LedgerApiMessage(
        message_id=2,
        target=1,
        performative=LedgerApiMessage.Performative.STATE,
        ledger_id=ledger_id,
        state=state,
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = LedgerApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_raw_transaction_serialization():
    """Test the serialization for 'raw_transaction' speech-act works."""
    msg = LedgerApiMessage(
        message_id=2,
        target=1,
        performative=LedgerApiMessage.Performative.RAW_TRANSACTION,
        raw_transaction=LedgerApiMessage.RawTransaction(
            "some_ledger_id", {"body": "some_body"}
        ),
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = LedgerApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_transaction_digest_serialization():
    """Test the serialization for 'transaction_digest' speech-act works."""
    msg = LedgerApiMessage(
        message_id=2,
        target=1,
        performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
        transaction_digest=LedgerApiMessage.TransactionDigest(
            "some_ledger_id", "some_body"
        ),
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = LedgerApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_transaction_receipt_serialization():
    """Test the serialization for 'transaction_receipt' speech-act works."""
    msg = LedgerApiMessage(
        message_id=2,
        target=1,
        performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
        transaction_receipt=LedgerApiMessage.TransactionReceipt(
            "some_ledger_id", {"key": "some_receipt"}, {"key": "some_transaction"}
        ),
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = LedgerApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_error_serialization():
    """Test the serialization for 'error' speech-act works."""
    msg = LedgerApiMessage(
        performative=LedgerApiMessage.Performative.ERROR,
        code=7,
        message="some_error_message",
        data=b"some_error_data",
    )
    msg.to = "receiver"
    envelope = Envelope(
        to=msg.to,
        sender="sender",
        message=msg,
    )
    envelope_bytes = envelope.encode()

    actual_envelope = Envelope.decode(envelope_bytes)
    expected_envelope = envelope
    assert expected_envelope.to == actual_envelope.to
    assert expected_envelope.sender == actual_envelope.sender
    assert (
        expected_envelope.protocol_specification_id
        == actual_envelope.protocol_specification_id
    )
    assert expected_envelope.message != actual_envelope.message

    actual_msg = LedgerApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_performative_string_value():
    """Test the string value of the performatives."""
    assert (
        str(LedgerApiMessage.Performative.GET_BALANCE) == "get_balance"
    ), "The str value must be get_balance"
    assert (
        str(LedgerApiMessage.Performative.GET_RAW_TRANSACTION) == "get_raw_transaction"
    ), "The str value must be get_raw_transaction"
    assert (
        str(LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION)
        == "send_signed_transaction"
    ), "The str value must be send_signed_transaction"
    assert (
        str(LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT)
        == "get_transaction_receipt"
    ), "The str value must be get_transaction_receipt"
    assert (
        str(LedgerApiMessage.Performative.BALANCE) == "balance"
    ), "The str value must be balance"
    assert (
        str(LedgerApiMessage.Performative.RAW_TRANSACTION) == "raw_transaction"
    ), "The str value must be raw_transaction"
    assert (
        str(LedgerApiMessage.Performative.TRANSACTION_DIGEST) == "transaction_digest"
    ), "The str value must be transaction_digest"
    assert (
        str(LedgerApiMessage.Performative.TRANSACTION_RECEIPT) == "transaction_receipt"
    ), "The str value must be transaction_receipt"
    assert (
        str(LedgerApiMessage.Performative.ERROR) == "error"
    ), "The str value must be error"


def test_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = LedgerApiMessage(
        performative=LedgerApiMessage.Performative.GET_BALANCE,
        ledger_id="some_ledger_id",
        address="some_address",
    )

    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(
            LedgerApiMessage.Performative, "__eq__", return_value=False
        ):
            LedgerApiMessage.serializer.encode(msg)


def test_decoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = LedgerApiMessage(
        performative=LedgerApiMessage.Performative.GET_BALANCE,
        ledger_id="some_ledger_id",
        address="some_address",
    )

    encoded_msg = LedgerApiMessage.serializer.encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(
            LedgerApiMessage.Performative, "__eq__", return_value=False
        ):
            LedgerApiMessage.serializer.decode(encoded_msg)


@mock.patch.object(
    message,
    "enforce",
    side_effect=AEAEnforceError("some error"),
)
def test_incorrect_message(mocked_enforce):
    """Test that we raise an exception when the message is incorrect."""
    with mock.patch.object(ledger_api_message_logger, "error") as mock_logger:
        LedgerApiMessage(
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id="some_ledger_id",
            address="some_address",
        )

        mock_logger.assert_any_call("some error")


class TestDialogues:
    """Tests ledger_api dialogues."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.agent_addr = "agent address"
        cls.ledger_addr = "ledger address"
        cls.agent_dialogues = AgentDialogues(cls.agent_addr)
        cls.ledger_dialogues = LedgerDialogues(cls.ledger_addr)

    def test_create_self_initiated(self):
        """Test the self initialisation of a dialogue."""
        result = self.agent_dialogues._create_self_initiated(
            dialogue_opponent_addr=self.ledger_addr,
            dialogue_reference=(str(0), ""),
            role=LedgerApiDialogue.Role.AGENT,
        )
        assert isinstance(result, LedgerApiDialogue)
        assert result.role == LedgerApiDialogue.Role.AGENT, "The role must be agent."

    def test_create_opponent_initiated(self):
        """Test the opponent initialisation of a dialogue."""
        result = self.agent_dialogues._create_opponent_initiated(
            dialogue_opponent_addr=self.ledger_addr,
            dialogue_reference=(str(0), ""),
            role=LedgerApiDialogue.Role.AGENT,
        )
        assert isinstance(result, LedgerApiDialogue)
        assert result.role == LedgerApiDialogue.Role.AGENT, "The role must be agen t."


class AgentDialogue(LedgerApiDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[LedgerApiMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        LedgerApiDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class AgentDialogues(LedgerApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom this dialogue is maintained
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return LedgerApiDialogue.Role.AGENT

        LedgerApiDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=AgentDialogue,
        )


class LedgerDialogue(LedgerApiDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[LedgerApiMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        LedgerApiDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class LedgerDialogues(LedgerApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom this dialogue is maintained
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return LedgerApiDialogue.Role.LEDGER

        LedgerApiDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=LedgerDialogue,
        )
