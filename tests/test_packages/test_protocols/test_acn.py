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

"""This module contains the tests of the messages module."""

from typing import Type
from unittest import mock
from unittest.mock import patch

import pytest

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

from packages.fetchai.protocols.acn.dialogues import AcnDialogue as BaseAcnDialogue
from packages.fetchai.protocols.acn.dialogues import AcnDialogues as BaseAcnDialogues
from packages.fetchai.protocols.acn.message import AcnMessage


def test_acn_aea_envelope_serialization():
    """Test that the serialization for the 'simple' protocol works for the AEA_ENVELOPE message."""
    expected_msg = AcnMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=AcnMessage.Performative.AEA_ENVELOPE,
        envelope=b"envelope",
        record=AcnMessage.AgentRecord(
            address="address",
            public_key="pbk",
            peer_public_key="peerpbk",
            signature="sign",
            service_id="acn",
            ledger_id="fetchai",
        ),
    )
    msg_bytes = AcnMessage.serializer.encode(expected_msg)
    actual_msg = AcnMessage.serializer.decode(msg_bytes)
    assert expected_msg == actual_msg


def test_acn_lookup_request_serialization():
    """Test that the serialization for the 'simple' protocol works for the LOOKUP_REQUEST message."""
    msg = AcnMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=AcnMessage.Performative.LOOKUP_REQUEST,
        agent_address="some_address",
    )
    msg_bytes = AcnMessage.serializer.encode(msg)
    actual_msg = AcnMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg


def test_acn_lookup_response_serialization():
    """Test that the serialization for the 'simple' protocol works for the LOOKUP_RESPONSE message."""
    msg = AcnMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=AcnMessage.Performative.LOOKUP_RESPONSE,
        record=AcnMessage.AgentRecord(
            address="address",
            public_key="pbk",
            peer_public_key="peerpbk",
            signature="sign",
            service_id="acn",
            ledger_id="fetchai",
        ),
    )
    msg_bytes = AcnMessage.serializer.encode(msg)
    actual_msg = AcnMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg


def test_acn_record_serialization():
    """Test that the serialization for the 'simple' protocol works for the REGISTER message."""
    msg = AcnMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=AcnMessage.Performative.REGISTER,
        record=AcnMessage.AgentRecord(
            address="address",
            public_key="pbk",
            peer_public_key="peerpbk",
            signature="sign",
            service_id="acn",
            ledger_id="fetchai",
        ),
    )
    msg_bytes = AcnMessage.serializer.encode(msg)
    actual_msg = AcnMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg


def test_acn_status_serialization():
    """Test that the serialization for the 'simple' protocol works for the STATUS message."""
    msg = AcnMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=AcnMessage.Performative.STATUS,
        body=AcnMessage.StatusBody(
            status_code=AcnMessage.StatusBody.StatusCode.ERROR_UNSUPPORTED_VERSION,
            msgs=["pbk"],
        ),
    )
    msg_bytes = AcnMessage.serializer.encode(msg)
    actual_msg = AcnMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg


def test_acn_message_str_values():
    """Tests the returned string values of acn Message."""
    assert (
        str(AcnMessage.Performative.LOOKUP_REQUEST) == "lookup_request"
    ), "AcnMessage.Performative.LOOKUP_REQUEST must be lookup_request"


def test_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = AcnMessage(
        performative=AcnMessage.Performative.LOOKUP_REQUEST, agent_address="address",
    )

    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(AcnMessage.Performative, "__eq__", return_value=False):
            AcnMessage.serializer.encode(msg)


def test_check_consistency_raises_exception_when_type_not_recognized():
    """Test that we raise exception when the type of the message is not recognized."""
    message = AcnMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=AcnMessage.Performative.LOOKUP_REQUEST,
        agent_address="address",
    )
    # mock the __eq__ method such that any kind of matching is going to fail.
    with mock.patch.object(AcnMessage.Performative, "__eq__", return_value=False):
        assert not message._is_consistent()


def test_acn_valid_performatives():
    """Test 'valid_performatives' getter."""
    msg = AcnMessage(AcnMessage.Performative.LOOKUP_REQUEST, agent_address="address")
    assert msg.valid_performatives == set(
        map(lambda x: x.value, iter(AcnMessage.Performative))
    )


def test_serializer_performative_not_found():
    """Test the serializer when the performative is not found."""
    message = AcnMessage(
        message_id=1,
        target=0,
        performative=AcnMessage.Performative.LOOKUP_REQUEST,
        agent_address="address",
    )
    message_bytes = message.serializer.encode(message)
    with patch.object(AcnMessage.Performative, "__eq__", return_value=False):
        with pytest.raises(ValueError, match="Performative not valid: .*"):
            message.serializer.decode(message_bytes)


def test_dialogues():
    """Test intiaontiation of dialogues."""
    acn_dialogues = AcnDialogues("agent_addr")
    msg, dialogue = acn_dialogues.create(
        counterparty="abc",
        performative=AcnMessage.Performative.LOOKUP_REQUEST,
        agent_address="address",
    )
    assert dialogue is not None


class AcnDialogue(BaseAcnDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[AcnMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        BaseAcnDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class AcnDialogues(BaseAcnDialogues):
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
            return AcnDialogue.Role.NODE

        BaseAcnDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=AcnDialogue,
        )
