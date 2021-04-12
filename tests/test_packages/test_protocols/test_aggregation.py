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

"""This module contains the tests of the aggregation protocol package."""

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
from packages.fetchai.protocols.aggregation.dialogues import (
    AggregationDialogue,
    AggregationDialogues,
)
from packages.fetchai.protocols.aggregation.message import AggregationMessage
from packages.fetchai.protocols.aggregation.message import (
    _default_logger as aggregation_message_logger,
)

from tests.conftest import ROOT_DIR


sys.path.append(ROOT_DIR)


def test_observation_serialization():
    """Test the serialization for 'observation' speech-act works."""
    msg = AggregationMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=AggregationMessage.Performative.OBSERVATION,
        value=0,
        time="some_time",
        source="some_source",
        signature="some_signature",
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

    actual_msg = AggregationMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_aggregation_serialization():
    """Test the serialization for 'aggregation' speech-act works."""
    msg = AggregationMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=AggregationMessage.Performative.AGGREGATION,
        value=0,
        time="some_time",
        contributors=("address1", "address2"),
        signature="some_multisignature",
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

    actual_msg = AggregationMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_performative_string_value():
    """Test the string value of the performatives."""
    assert (
        str(AggregationMessage.Performative.OBSERVATION) == "observation"
    ), "The str value must be observation"
    assert (
        str(AggregationMessage.Performative.AGGREGATION) == "aggregation"
    ), "The str value must be aggregation"


def test_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = AggregationMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=AggregationMessage.Performative.AGGREGATION,
        value=0,
        time="some_time",
        contributors=("address1", "address2"),
        signature="some_multisignature",
    )

    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(
            AggregationMessage.Performative, "__eq__", return_value=False
        ):
            AggregationMessage.serializer.encode(msg)


def test_decoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = AggregationMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=AggregationMessage.Performative.AGGREGATION,
        value=0,
        time="some_time",
        contributors=("address1", "address2"),
        signature="some_multisignature",
    )

    encoded_msg = AggregationMessage.serializer.encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(
            AggregationMessage.Performative, "__eq__", return_value=False
        ):
            AggregationMessage.serializer.decode(encoded_msg)


@mock.patch.object(
    packages.fetchai.protocols.aggregation.message,
    "enforce",
    side_effect=AEAEnforceError("some error"),
)
def test_incorrect_message(mocked_enforce):
    """Test that we raise an exception when the message is incorrect."""
    with mock.patch.object(aggregation_message_logger, "error") as mock_logger:
        AggregationMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=AggregationMessage.Performative.AGGREGATION,
        )

        mock_logger.assert_any_call("some error")


class TestDialogues:
    """Tests aggregation dialogues."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.agent_addr = "agent address"
        cls.peer_addr = "peer address"
        cls.agent_dialogues = AgentDialogues(cls.agent_addr)
        cls.server_dialogues = PeerDialogues(cls.peer_addr)

    def test_create_self_initiated(self):
        """Test the self initialisation of a dialogue."""
        result = self.agent_dialogues._create_self_initiated(
            dialogue_opponent_addr=self.peer_addr,
            dialogue_reference=(str(0), ""),
            role=AggregationDialogue.Role.AGENT,
        )
        assert isinstance(result, AggregationDialogue)
        assert result.role == AggregationDialogue.Role.AGENT, "The role must be Agent."

    def test_create_opponent_initiated(self):
        """Test the opponent initialisation of a dialogue."""
        result = self.agent_dialogues._create_opponent_initiated(
            dialogue_opponent_addr=self.peer_addr,
            dialogue_reference=(str(0), ""),
            role=AggregationDialogue.Role.AGENT,
        )
        assert isinstance(result, AggregationDialogue)
        assert result.role == AggregationDialogue.Role.AGENT, "The role must be Agent."


class AgentDialogue(AggregationDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[AggregationMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        AggregationDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class AgentDialogues(AggregationDialogues):
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
            return AggregationDialogue.Role.AGENT

        AggregationDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=AgentDialogue,
        )


class PeerDialogue(AggregationDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[AggregationMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        AggregationDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class PeerDialogues(AggregationDialogues):
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
            return AggregationDialogue.Role.AGENT

        AggregationDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=PeerDialogue,
        )
