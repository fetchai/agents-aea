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

"""This module contains the tests of the oef_search protocol package."""

import sys
from typing import Type
from unittest import mock

import pytest

from aea.common import Address
from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

import packages
from packages.fetchai.protocols.oef_search.dialogues import (
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.oef_search.message import (
    _default_logger as oef_search_message_logger,
)

from tests.conftest import ROOT_DIR


sys.path.append(ROOT_DIR)


def test_register_service_serialization():
    """Test the serialization for 'register_service' speech-act works."""
    msg = OefSearchMessage(
        performative=OefSearchMessage.Performative.REGISTER_SERVICE,
        service_description=Description({"foo1": 1, "bar1": 2}),
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

    actual_msg = OefSearchMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_unregister_service_serialization():
    """Test the serialization for 'unregister_service' speech-act works."""
    msg = OefSearchMessage(
        message_id=2,
        target=1,
        performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
        service_description=Description({"foo1": 1, "bar1": 2}),
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

    actual_msg = OefSearchMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_search_services_serialization():
    """Test the serialization for 'search_services' speech-act works."""
    msg = OefSearchMessage(
        performative=OefSearchMessage.Performative.SEARCH_SERVICES,
        query=Query([Constraint("something", ConstraintType(">", 1))]),
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

    actual_msg = OefSearchMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_search_result_serialization():
    """Test the serialization for 'search_result' speech-act works."""
    msg = OefSearchMessage(
        performative=OefSearchMessage.Performative.SEARCH_RESULT,
        agents=("agent_1", "agent_2", "agent_3"),
        agents_info=OefSearchMessage.AgentsInfo(
            {
                "key_1": {"key_1": b"value_1", "key_2": b"value_2"},
                "key_2": {"key_3": b"value_3", "key_4": b"value_4"},
            }
        ),
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

    actual_msg = OefSearchMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_success_serialization():
    """Test the serialization for 'success' speech-act works."""
    msg = OefSearchMessage(
        performative=OefSearchMessage.Performative.SUCCESS,
        agents_info=OefSearchMessage.AgentsInfo(
            {
                "key_1": {"key_1": b"value_1", "key_2": b"value_2"},
                "key_2": {"key_3": b"value_3", "key_4": b"value_4"},
            }
        ),
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

    actual_msg = OefSearchMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_oef_error_serialization():
    """Test the serialization for 'oef_error' speech-act works."""
    msg = OefSearchMessage(
        performative=OefSearchMessage.Performative.OEF_ERROR,
        oef_error_operation=OefSearchMessage.OefErrorOperation.OTHER,
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

    actual_msg = OefSearchMessage.serializer.decode(actual_envelope.message)
    actual_msg.to = actual_envelope.to
    actual_msg.sender = actual_envelope.sender
    expected_msg = msg
    assert expected_msg == actual_msg


def test_oef_type_string_value():
    """Test the string value of the type."""
    assert (
        str(OefSearchMessage.Performative.REGISTER_SERVICE) == "register_service"
    ), "The str value must be register_service"
    assert (
        str(OefSearchMessage.Performative.UNREGISTER_SERVICE) == "unregister_service"
    ), "The str value must be unregister_service"
    assert (
        str(OefSearchMessage.Performative.SEARCH_SERVICES) == "search_services"
    ), "The str value must be search_services"
    assert (
        str(OefSearchMessage.Performative.OEF_ERROR) == "oef_error"
    ), "The str value must be oef_error"
    assert (
        str(OefSearchMessage.Performative.SEARCH_RESULT) == "search_result"
    ), "The str value must be search_result"


def test_oef_error_operation():
    """Test the string value of the error operation."""
    assert (
        str(OefSearchMessage.OefErrorOperation.REGISTER_SERVICE) == "0"
    ), "The str value must be 0"
    assert (
        str(OefSearchMessage.OefErrorOperation.UNREGISTER_SERVICE) == "1"
    ), "The str value must be 1"
    assert (
        str(OefSearchMessage.OefErrorOperation.SEARCH_SERVICES) == "2"
    ), "The str value must be 2"
    assert (
        str(OefSearchMessage.OefErrorOperation.SEND_MESSAGE) == "3"
    ), "The str value must be 3"
    assert (
        str(OefSearchMessage.OefErrorOperation.OTHER) == "10000"
    ), "The str value must be 10000"


def test_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = OefSearchMessage(
        performative=OefSearchMessage.Performative.REGISTER_SERVICE,
        service_description=Description({"foo1": 1, "bar1": 2}),
    )

    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(
            OefSearchMessage.Performative, "__eq__", return_value=False
        ):
            OefSearchMessage.serializer.encode(msg)


def test_decoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during decoding."""
    msg = OefSearchMessage(
        performative=OefSearchMessage.Performative.REGISTER_SERVICE,
        service_description=Description({"foo1": 1, "bar1": 2}),
    )

    encoded_msg = OefSearchMessage.serializer.encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(
            OefSearchMessage.Performative, "__eq__", return_value=False
        ):
            OefSearchMessage.serializer.decode(encoded_msg)


@mock.patch.object(
    packages.fetchai.protocols.oef_search.message,
    "enforce",
    side_effect=AEAEnforceError("some error"),
)
def test_incorrect_message(mocked_enforce):
    """Test that we raise an exception when the fipa message is incorrect."""
    with mock.patch.object(oef_search_message_logger, "error") as mock_logger:
        OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=Description({"foo1": 1, "bar1": 2}),
        )

        mock_logger.assert_any_call("some error")


def test_agent_info():
    """Test the agent_info custom type."""
    agents_info = OefSearchMessage.AgentsInfo(
        {
            "agent_address_1": {"key_1": b"value_1", "key_2": b"value_2"},
            "agent_address_2": {"key_3": b"value_3", "key_4": b"value_4"},
        }
    )
    assert agents_info.get_info_for_agent("agent_address_1") == {
        "key_1": b"value_1",
        "key_2": b"value_2",
    }

    with pytest.raises(ValueError, match="body must not be None"):
        OefSearchMessage.AgentsInfo(None)


class TestDialogues:
    """Tests oef_search dialogues."""

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        cls.agent_addr = "agent address"
        cls.oef_node_addr = "oef_node address"
        cls.agent_dialogues = BuyerDialogues(cls.agent_addr)
        cls.oef_node_dialogues = OEFNodeDialogues(cls.oef_node_addr)

    def test_create_self_initiated(self):
        """Test the self initialisation of a dialogue."""
        result = self.agent_dialogues._create_self_initiated(
            dialogue_opponent_addr=self.oef_node_addr,
            dialogue_reference=(str(0), ""),
            role=OefSearchDialogue.Role.AGENT,
        )
        assert isinstance(result, OefSearchDialogue)
        assert result.role == OefSearchDialogue.Role.AGENT, "The role must be agent."

    def test_create_opponent_initiated(self):
        """Test the opponent initialisation of a dialogue."""
        result = self.agent_dialogues._create_opponent_initiated(
            dialogue_opponent_addr=self.oef_node_addr,
            dialogue_reference=(str(0), ""),
            role=OefSearchDialogue.Role.AGENT,
        )
        assert isinstance(result, OefSearchDialogue)
        assert result.role == OefSearchDialogue.Role.AGENT, "The role must be agent."


class BuyerDialogue(OefSearchDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[OefSearchMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        OefSearchDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class BuyerDialogues(OefSearchDialogues):
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
            return OefSearchDialogue.Role.AGENT

        OefSearchDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=BuyerDialogue,
        )


class OEFNodeDialogue(OefSearchDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[OefSearchMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        OefSearchDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class OEFNodeDialogues(OefSearchDialogues):
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
            return OefSearchDialogue.Role.OEF_NODE

        OefSearchDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=OEFNodeDialogue,
        )
