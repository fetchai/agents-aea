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

"""This module contains the tests of the http protocol package."""

import sys
from typing import Type
from unittest import mock

import pytest

from aea.common import Address
from aea.exceptions import AEAEnforceError
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

import packages
from packages.fetchai.protocols.tac.dialogues import TacDialogue, TacDialogues
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.protocols.tac.message import _default_logger as tac_message_logger

from tests.conftest import ROOT_DIR


sys.path.append(ROOT_DIR)


def test_tac_message_instantiation():
    """Test instantiation of the tac message."""
    assert TacMessage(
        performative=TacMessage.Performative.REGISTER, agent_name="some_name"
    )
    assert TacMessage(performative=TacMessage.Performative.UNREGISTER)
    assert TacMessage(
        performative=TacMessage.Performative.TRANSACTION,
        transaction_id="some_id",
        ledger_id="some_ledger",
        sender_address="some_address",
        counterparty_address="some_other_address",
        amount_by_currency_id={"FET": 10},
        fee_by_currency_id={"FET": 1},
        quantities_by_good_id={"123": 0, "1234": 10},
        nonce=1,
        sender_signature="some_signature",
        counterparty_signature="some_other_signature",
    )
    assert TacMessage(performative=TacMessage.Performative.CANCELLED)
    assert TacMessage(
        performative=TacMessage.Performative.GAME_DATA,
        amount_by_currency_id={"FET": 10},
        exchange_params_by_currency_id={"FET": 10.0},
        quantities_by_good_id={"123": 20, "1234": 15},
        utility_params_by_good_id={"123": 30.0, "1234": 50.0},
        fee_by_currency_id={"FET": 1},
        agent_addr_to_name={"agent_1": "Agent one", "agent_2": "Agent two"},
        currency_id_to_name={"FET": "currency_name"},
        good_id_to_name={"123": "First good", "1234": "Second good"},
        version_id="game_version_1",
    )
    assert TacMessage(
        performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
        transaction_id="some_id",
        amount_by_currency_id={"FET": 10},
        quantities_by_good_id={"123": 20, "1234": 15},
    )
    assert TacMessage(
        performative=TacMessage.Performative.TAC_ERROR,
        error_code=TacMessage.ErrorCode.GENERIC_ERROR,
        info={"msg": "This is info msg."},
    )
    assert str(TacMessage.Performative.REGISTER) == "register"


def test_register_serialization():
    """Test the serialization for 'register' speech-act works."""
    msg = TacMessage(
        performative=TacMessage.Performative.REGISTER, agent_name="some_agent_name",
    )
    msg.to = "receiver"
    envelope = Envelope(to=msg.to, sender="sender", message=msg,)
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

    actual_msg = TacMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_unregister_serialization():
    """Test the serialization for 'unregister' speech-act works."""
    msg = TacMessage(
        message_id=2, target=1, performative=TacMessage.Performative.UNREGISTER,
    )
    msg.to = "receiver"
    envelope = Envelope(to=msg.to, sender="sender", message=msg,)
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

    actual_msg = TacMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_transaction_serialization():
    """Test the serialization for 'transaction' speech-act works."""
    msg = TacMessage(
        performative=TacMessage.Performative.TRANSACTION,
        transaction_id="some_transaction_id",
        ledger_id="some_ledger_id",
        sender_address="some_sender_address",
        counterparty_address="some_counterparty_address",
        amount_by_currency_id={"key_1": 1, "key_2": 2},
        fee_by_currency_id={"key_1": 1, "key_2": 2},
        quantities_by_good_id={"key_1": 1, "key_2": 2},
        nonce="some_nonce",
        sender_signature="some_sender_signature",
        counterparty_signature="some_counterparty_signature",
    )
    msg.to = "receiver"
    envelope = Envelope(to=msg.to, sender="sender", message=msg,)
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

    actual_msg = TacMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_cancelled_serialization():
    """Test the serialization for 'cancelled' speech-act works."""
    msg = TacMessage(performative=TacMessage.Performative.CANCELLED,)
    msg.to = "receiver"
    envelope = Envelope(to=msg.to, sender="sender", message=msg,)
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

    actual_msg = TacMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_game_data_serialization():
    """Test the serialization for 'game_data' speech-act works."""
    msg = TacMessage(
        performative=TacMessage.Performative.GAME_DATA,
        amount_by_currency_id={"key_1": 1, "key_2": 2},
        exchange_params_by_currency_id={"key_1": 1.0, "key_2": 2.0},
        quantities_by_good_id={"key_1": 1, "key_2": 2},
        utility_params_by_good_id={"key_1": 1.0, "key_2": 2.0},
        fee_by_currency_id={"key_1": 1, "key_2": 2},
        agent_addr_to_name={"key_1": "value_1", "key_2": "value_2"},
        currency_id_to_name={"key_1": "value_1", "key_2": "value_2"},
        good_id_to_name={"key_1": "value_1", "key_2": "value_2"},
        version_id="some_version_id",
        info={"key_1": "value_1", "key_2": "value_2"},
    )
    msg.to = "receiver"
    envelope = Envelope(to=msg.to, sender="sender", message=msg,)
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

    actual_msg = TacMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_transaction_confirmation_serialization():
    """Test the serialization for 'transaction_confirmation' speech-act works."""
    msg = TacMessage(
        performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
        transaction_id="some_transaction_id",
        amount_by_currency_id={"key_1": 1, "key_2": 2},
        quantities_by_good_id={"key_1": 1, "key_2": 2},
    )
    msg.to = "receiver"
    envelope = Envelope(to=msg.to, sender="sender", message=msg,)
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

    actual_msg = TacMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_tac_error_serialization():
    """Test the serialization for 'tac_error' speech-act works."""
    msg = TacMessage(
        performative=TacMessage.Performative.TAC_ERROR,
        error_code=TacMessage.ErrorCode.GENERIC_ERROR,
        info={"key_1": "value_1", "key_2": "value_2"},
    )
    msg.to = "receiver"
    envelope = Envelope(to=msg.to, sender="sender", message=msg,)
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

    actual_msg = TacMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_oef_type_string_value():
    """Test the string value of the type."""
    assert (
        str(TacMessage.Performative.REGISTER) == "register"
    ), "The str value must be register"
    assert (
        str(TacMessage.Performative.UNREGISTER) == "unregister"
    ), "The str value must be unregister"
    assert (
        str(TacMessage.Performative.TRANSACTION) == "transaction"
    ), "The str value must be transaction"
    assert (
        str(TacMessage.Performative.CANCELLED) == "cancelled"
    ), "The str value must be cancelled"
    assert (
        str(TacMessage.Performative.GAME_DATA) == "game_data"
    ), "The str value must be game_data"
    assert (
        str(TacMessage.Performative.TRANSACTION_CONFIRMATION)
        == "transaction_confirmation"
    ), "The str value must be transaction_confirmation"
    assert (
        str(TacMessage.Performative.TAC_ERROR) == "tac_error"
    ), "The str value must be tac_error"


def test_error_code_to_msg():
    """Test the serialization for 'tac_error' speech-act works."""

    assert (
        str(TacMessage.ErrorCode.to_msg(0)) == "Unexpected error."
    ), 'The str value must be "Unexpected error."'
    assert (
        str(TacMessage.ErrorCode.to_msg(1)) == "Request not recognized"
    ), 'The str value must be "Request not recognized"'
    assert (
        str(TacMessage.ErrorCode.to_msg(2)) == "Agent addr already registered."
    ), 'The str value must be "Agent addr already registered."'
    assert (
        str(TacMessage.ErrorCode.to_msg(3)) == "Agent name already registered."
    ), 'The str value must be "Agent name already registered."'
    assert (
        str(TacMessage.ErrorCode.to_msg(4)) == "Agent not registered."
    ), 'The str value must be "Agent not registered."'
    assert (
        str(TacMessage.ErrorCode.to_msg(5)) == "Error in checking transaction"
    ), 'The str value must be "Error in checking transaction"'
    assert (
        str(TacMessage.ErrorCode.to_msg(6))
        == "The transaction request does not match with a previous transaction request with the same id."
    ), 'The str value must be "The transaction request does not match with a previous transaction request with the same id."'
    assert (
        str(TacMessage.ErrorCode.to_msg(7)) == "Agent name not in whitelist."
    ), 'The str value must be "Agent name not in whitelist."'
    assert (
        str(TacMessage.ErrorCode.to_msg(8)) == "The competition is not running yet."
    ), 'The str value must be "The competition is not running yet."'
    assert (
        str(TacMessage.ErrorCode.to_msg(9))
        == "The message is inconsistent with the dialogue."
    ), 'The str value must be "The message is inconsistent with the dialogue."'


def test_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = TacMessage(performative=TacMessage.Performative.CANCELLED,)

    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(TacMessage.Performative, "__eq__", return_value=False):
            TacMessage.serializer.encode(msg)


def test_decoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = TacMessage(performative=TacMessage.Performative.CANCELLED,)

    encoded_msg = TacMessage.serializer.encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(TacMessage.Performative, "__eq__", return_value=False):
            TacMessage.serializer.decode(encoded_msg)


@mock.patch.object(
    packages.fetchai.protocols.tac.message,
    "enforce",
    side_effect=AEAEnforceError("some error"),
)
def test_incorrect_message(mocked_enforce):
    """Test that we raise an exception when the message is incorrect."""
    with mock.patch.object(tac_message_logger, "error") as mock_logger:
        TacMessage(performative=TacMessage.Performative.CANCELLED,)

        mock_logger.assert_any_call("some error")


class TestDialogues:
    """Tests tac dialogues."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.agent_addr = "agent address"
        cls.controller_addr = "controller address"
        cls.agent_dialogues = AgentDialogues(cls.agent_addr)
        cls.controller_dialogues = ControllerDialogues(cls.controller_addr)

    def test_create_self_initiated(self):
        """Test the self initialisation of a dialogue."""
        result = self.agent_dialogues._create_self_initiated(
            dialogue_opponent_addr=self.controller_addr,
            dialogue_reference=(str(0), ""),
            role=TacDialogue.Role.PARTICIPANT,
        )
        assert isinstance(result, TacDialogue)
        assert (
            result.role == TacDialogue.Role.PARTICIPANT
        ), "The role must be participant."

    def test_create_opponent_initiated(self):
        """Test the opponent initialisation of a dialogue."""
        result = self.agent_dialogues._create_opponent_initiated(
            dialogue_opponent_addr=self.controller_addr,
            dialogue_reference=(str(0), ""),
            role=TacDialogue.Role.PARTICIPANT,
        )
        assert isinstance(result, TacDialogue)
        assert (
            result.role == TacDialogue.Role.PARTICIPANT
        ), "The role must be participant."


class AgentDialogue(TacDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[TacMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        TacDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class AgentDialogues(TacDialogues):
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
            return TacDialogue.Role.PARTICIPANT

        TacDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=AgentDialogue,
        )


class ControllerDialogue(TacDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[TacMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        TacDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class ControllerDialogues(TacDialogues):
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
            return TacDialogue.Role.CONTROLLER

        TacDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=ControllerDialogue,
        )
