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

"""This module contains the tests of the gym protocol package."""
# pylint: skip-file

from typing import Type
from unittest import mock

import pytest

from aea.common import Address
from aea.exceptions import AEAEnforceError
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

from packages.fetchai.protocols.gym import message
from packages.fetchai.protocols.gym.dialogues import GymDialogue, GymDialogues
from packages.fetchai.protocols.gym.message import GymMessage
from packages.fetchai.protocols.gym.message import _default_logger as gym_message_logger


def test_act_serialization():
    """Test the serialization for 'act' speech-act works."""
    msg = GymMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=GymMessage.Performative.ACT,
        action=GymMessage.AnyObject("some_action"),
        step_id=1,
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

    actual_msg = GymMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_percept_serialization():
    """Test the serialization for 'percept' speech-act works."""
    msg = GymMessage(
        message_id=2,
        dialogue_reference=(str(0), ""),
        target=1,
        performative=GymMessage.Performative.PERCEPT,
        step_id=1,
        observation=GymMessage.AnyObject("some_observation"),
        reward=10.0,
        done=False,
        info=GymMessage.AnyObject("some_info"),
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

    actual_msg = GymMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_status_serialization():
    """Test the serialization for 'status' speech-act works."""
    content_arg = {
        "key_1": "value_1",
        "key_2": "value_2",
    }
    msg = GymMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=GymMessage.Performative.STATUS,
        content=content_arg,
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

    actual_msg = GymMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_reset_serialization():
    """Test the serialization for 'reset' speech-act works."""
    msg = GymMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=GymMessage.Performative.RESET,
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

    actual_msg = GymMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_close_serialization():
    """Test the serialization for 'close' speech-act works."""
    msg = GymMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=GymMessage.Performative.CLOSE,
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

    actual_msg = GymMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_performative_string_value():
    """Test the string value of the performatives."""
    assert str(GymMessage.Performative.ACT) == "act", "The str value must be act"
    assert (
        str(GymMessage.Performative.PERCEPT) == "percept"
    ), "The str value must be percept"
    assert (
        str(GymMessage.Performative.STATUS) == "status"
    ), "The str value must be status"
    assert str(GymMessage.Performative.RESET) == "reset", "The str value must be reset"
    assert str(GymMessage.Performative.CLOSE) == "close", "The str value must be close"


def test_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = GymMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=GymMessage.Performative.RESET,
    )

    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(GymMessage.Performative, "__eq__", return_value=False):
            GymMessage.serializer.encode(msg)


def test_decoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = GymMessage(
        message_id=1,
        dialogue_reference=(str(0), ""),
        target=0,
        performative=GymMessage.Performative.RESET,
    )

    encoded_msg = GymMessage.serializer.encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(GymMessage.Performative, "__eq__", return_value=False):
            GymMessage.serializer.decode(encoded_msg)


@mock.patch.object(
    message,
    "enforce",
    side_effect=AEAEnforceError("some error"),
)
def test_incorrect_message(mocked_enforce):
    """Test that we raise an exception when the message is incorrect."""
    with mock.patch.object(gym_message_logger, "error") as mock_logger:
        GymMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=GymMessage.Performative.RESET,
        )

        mock_logger.assert_any_call("some error")


class TestDialogues:
    """Tests gym dialogues."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.agent_addr = "agent address"
        cls.env_addr = "env address"
        cls.agent_dialogues = AgentDialogues(cls.agent_addr)
        cls.env_dialogues = EnvironmentDialogues(cls.env_addr)

    def test_create_self_initiated(self):
        """Test the self initialisation of a dialogue."""
        result = self.agent_dialogues._create_self_initiated(
            dialogue_opponent_addr=self.env_addr,
            dialogue_reference=(str(0), ""),
            role=GymDialogue.Role.AGENT,
        )
        assert isinstance(result, GymDialogue)
        assert result.role == GymDialogue.Role.AGENT, "The role must be Agent."

    def test_create_opponent_initiated(self):
        """Test the opponent initialisation of a dialogue."""
        result = self.agent_dialogues._create_opponent_initiated(
            dialogue_opponent_addr=self.env_addr,
            dialogue_reference=(str(0), ""),
            role=GymDialogue.Role.AGENT,
        )
        assert isinstance(result, GymDialogue)
        assert result.role == GymDialogue.Role.AGENT, "The role must be agent."


class AgentDialogue(GymDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[GymMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        GymDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class AgentDialogues(GymDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom this dialogues is maintained
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return GymDialogue.Role.AGENT

        GymDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=AgentDialogue,
        )


class EnvironmentDialogue(GymDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[GymMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        GymDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class EnvironmentDialogues(GymDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom this dialogues is maintained
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return GymDialogue.Role.ENVIRONMENT

        GymDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=EnvironmentDialogue,
        )
