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

"""This module contains the tests of the contract_api protocol package."""

import logging
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
from packages.fetchai.protocols.contract_api.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
)
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.contract_api.message import (
    _default_logger as contract_api_message_logger,
)

from tests.conftest import ROOT_DIR


logger = logging.getLogger(__name__)
sys.path.append(ROOT_DIR)


def test_get_deploy_transaction_serialization():
    """Test the serialization for 'get_deploy_transaction' speech-act works."""
    kwargs_arg = ContractApiMessage.Kwargs({"key_1": 1, "key_2": 2})
    msg = ContractApiMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
        ledger_id="some_ledger_id",
        contract_id="some_contract_id",
        callable="some_callable",
        kwargs=kwargs_arg,
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

    actual_msg = ContractApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_get_raw_transaction_serialization():
    """Test the serialization for 'get_raw_transaction' speech-act works."""
    kwargs_arg = ContractApiMessage.Kwargs({"key_1": 1, "key_2": 2})
    msg = ContractApiMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
        ledger_id="some_ledger_id",
        contract_id="some_contract_id",
        contract_address="some_contract_address",
        callable="some_callable",
        kwargs=kwargs_arg,
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

    actual_msg = ContractApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_get_raw_message_serialization():
    """Test the serialization for 'get_raw_message' speech-act works."""
    kwargs_arg = ContractApiMessage.Kwargs({"key_1": 1, "key_2": 2})
    msg = ContractApiMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=ContractApiMessage.Performative.GET_RAW_MESSAGE,
        ledger_id="some_ledger_id",
        contract_id="some_contract_id",
        contract_address="some_contract_address",
        callable="some_callable",
        kwargs=kwargs_arg,
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

    actual_msg = ContractApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_get_state_serialization():
    """Test the serialization for 'get_state' speech-act works."""
    kwargs_arg = ContractApiMessage.Kwargs({"key_1": 1, "key_2": 2})
    msg = ContractApiMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=ContractApiMessage.Performative.GET_STATE,
        ledger_id="some_ledger_id",
        contract_id="some_contract_id",
        contract_address="some_contract_address",
        callable="some_callable",
        kwargs=kwargs_arg,
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

    actual_msg = ContractApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_state_serialization():
    """Test the serialization for 'state' speech-act works."""
    state_arg = ContractApiMessage.State("some_ledger_id", {"key": "some_body"})
    msg = ContractApiMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=ContractApiMessage.Performative.STATE,
        state=state_arg,
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

    actual_msg = ContractApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_raw_transaction_serialization():
    """Test the serialization for 'raw_transaction' speech-act works."""
    raw_transaction_arg = ContractApiMessage.RawTransaction(
        "some_ledger_id", {"body": "some_body"}
    )
    msg = ContractApiMessage(
        message_id=2,
        target=1,
        performative=ContractApiMessage.Performative.RAW_TRANSACTION,
        raw_transaction=raw_transaction_arg,
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

    actual_msg = ContractApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_raw_message_serialization():
    """Test the serialization for 'raw_message' speech-act works."""
    raw_message_arg = ContractApiMessage.RawMessage("some_ledger_id", b"some_body")
    msg = ContractApiMessage(
        performative=ContractApiMessage.Performative.RAW_MESSAGE,
        raw_message=raw_message_arg,
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

    actual_msg = ContractApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_error_serialization():
    """Test the serialization for 'error' speech-act works."""
    msg = ContractApiMessage(
        performative=ContractApiMessage.Performative.ERROR,
        code=7,
        message="some_error_message",
        data=b"some_error_data",
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

    actual_msg = ContractApiMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_performative_string_value():
    """Test the string value of the performatives."""
    assert (
        str(ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION)
        == "get_deploy_transaction"
    ), "The str value must be get_deploy_transaction"
    assert (
        str(ContractApiMessage.Performative.GET_RAW_TRANSACTION)
        == "get_raw_transaction"
    ), "The str value must be get_raw_transaction"
    assert (
        str(ContractApiMessage.Performative.GET_RAW_MESSAGE) == "get_raw_message"
    ), "The str value must be get_raw_message"
    assert (
        str(ContractApiMessage.Performative.GET_STATE) == "get_state"
    ), "The str value must be get_state"
    assert (
        str(ContractApiMessage.Performative.STATE) == "state"
    ), "The str value must be state"
    assert (
        str(ContractApiMessage.Performative.RAW_TRANSACTION) == "raw_transaction"
    ), "The str value must be raw_transaction"
    assert (
        str(ContractApiMessage.Performative.RAW_MESSAGE) == "raw_message"
    ), "The str value must be raw_message"
    assert (
        str(ContractApiMessage.Performative.ERROR) == "error"
    ), "The str value must be error"


def test_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = ContractApiMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=ContractApiMessage.Performative.RAW_MESSAGE,
        raw_message=ContractApiMessage.RawMessage("some_ledger_id", b"some_body"),
    )

    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(
            ContractApiMessage.Performative, "__eq__", return_value=False
        ):
            ContractApiMessage.serializer.encode(msg)


def test_decoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = ContractApiMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=ContractApiMessage.Performative.RAW_MESSAGE,
        raw_message=ContractApiMessage.RawMessage("some_ledger_id", b"some_body"),
    )

    encoded_msg = ContractApiMessage.serializer.encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(
            ContractApiMessage.Performative, "__eq__", return_value=False
        ):
            ContractApiMessage.serializer.decode(encoded_msg)


@mock.patch.object(
    packages.fetchai.protocols.contract_api.message,
    "enforce",
    side_effect=AEAEnforceError("some error"),
)
def test_incorrect_message(mocked_enforce):
    """Test that we raise an exception when the message is incorrect."""
    with mock.patch.object(contract_api_message_logger, "error") as mock_logger:
        ContractApiMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=ContractApiMessage.Performative.RAW_MESSAGE,
            raw_message=ContractApiMessage.RawMessage("some_ledger_id", b"some_body"),
        )

        mock_logger.assert_any_call("some error")


def test_kwargs():
    """Test the kwargs custom type."""
    body = {"key_1": 1, "key_2": 2}
    kwargs = ContractApiMessage.Kwargs(body)
    assert str(kwargs) == "Kwargs: body={}".format(body)


class TestDialogues:
    """Tests contract_api dialogues."""

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
            role=ContractApiDialogue.Role.AGENT,
        )
        assert isinstance(result, ContractApiDialogue)
        assert result.role == ContractApiDialogue.Role.AGENT, "The role must be Agent."

    def test_create_opponent_initiated(self):
        """Test the opponent initialisation of a dialogue."""
        result = self.agent_dialogues._create_opponent_initiated(
            dialogue_opponent_addr=self.ledger_addr,
            dialogue_reference=(str(0), ""),
            role=ContractApiDialogue.Role.AGENT,
        )
        assert isinstance(result, ContractApiDialogue)
        assert result.role == ContractApiDialogue.Role.AGENT, "The role must be agent."


class AgentDialogue(ContractApiDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[ContractApiMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        ContractApiDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class AgentDialogues(ContractApiDialogues):
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
            return ContractApiDialogue.Role.AGENT

        ContractApiDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=AgentDialogue,
        )


class LedgerDialogue(ContractApiDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[ContractApiMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        ContractApiDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class LedgerDialogues(ContractApiDialogues):
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
            return ContractApiDialogue.Role.LEDGER

        ContractApiDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=LedgerDialogue,
        )
