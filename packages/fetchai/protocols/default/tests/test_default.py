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
from unittest.mock import patch

import pytest

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogue as BaseDefaultDialogue,
)
from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogues as BaseDefaultDialogues,
)
from packages.fetchai.protocols.default.message import DefaultMessage


def test_default_bytes_serialization():
    """Test that the serialization for the 'simple' protocol works for the BYTES message."""
    expected_msg = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"hello",
    )
    msg_bytes = DefaultMessage.serializer.encode(expected_msg)
    actual_msg = DefaultMessage.serializer.decode(msg_bytes)
    assert expected_msg == actual_msg


def test_default_error_serialization():
    """Test that the serialization for the 'simple' protocol works for the ERROR message."""
    msg = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.ERROR,
        error_code=DefaultMessage.ErrorCode.UNSUPPORTED_PROTOCOL,
        error_msg="An error",
        error_data={"error": b"Some error data"},
    )
    msg_bytes = DefaultMessage.serializer.encode(msg)
    actual_msg = DefaultMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg


def test_default_end_serialization():
    """Test that the serialization for the 'simple' protocol works for the END message."""
    msg = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.END,
    )
    msg_bytes = DefaultMessage.serializer.encode(msg)
    actual_msg = DefaultMessage.serializer.decode(msg_bytes)
    expected_msg = msg
    assert expected_msg == actual_msg


def test_default_message_str_values():
    """Tests the returned string values of default Message."""
    assert (
        str(DefaultMessage.Performative.BYTES) == "bytes"
    ), "DefaultMessage.Performative.BYTES must be bytes"
    assert (
        str(DefaultMessage.Performative.ERROR) == "error"
    ), "DefaultMessage.Performative.ERROR must be error"


def test_encoding_unknown_performative():
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = DefaultMessage(
        performative=DefaultMessage.Performative.BYTES, content=b"hello"
    )

    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(
            DefaultMessage.Performative, "__eq__", return_value=False
        ):
            DefaultMessage.serializer.encode(msg)


def test_check_consistency_raises_exception_when_type_not_recognized():
    """Test that we raise exception when the type of the message is not recognized."""
    message = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"hello",
    )
    # mock the __eq__ method such that any kind of matching is going to fail.
    with mock.patch.object(DefaultMessage.Performative, "__eq__", return_value=False):
        assert not message._is_consistent()


def test_default_valid_performatives():
    """Test 'valid_performatives' getter."""
    msg = DefaultMessage(DefaultMessage.Performative.BYTES, content=b"")
    assert msg.valid_performatives == set(
        map(lambda x: x.value, iter(DefaultMessage.Performative))
    )


def test_serializer_performative_not_found():
    """Test the serializer when the performative is not found."""
    message = DefaultMessage(
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"",
    )
    message_bytes = message.serializer.encode(message)
    with patch.object(DefaultMessage.Performative, "__eq__", return_value=False):
        with pytest.raises(ValueError, match="Performative not valid: .*"):
            message.serializer.decode(message_bytes)


def test_dialogues():
    """Test intiaontiation of dialogues."""
    default_dialogues = DefaultDialogues("agent_addr")
    msg, dialogue = default_dialogues.create(
        counterparty="abc",
        performative=DefaultMessage.Performative.BYTES,
        content=b"hello",
    )
    assert dialogue is not None


class DefaultDialogue(BaseDefaultDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[DefaultMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        BaseDefaultDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class DefaultDialogues(BaseDefaultDialogues):
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
            return DefaultDialogue.Role.AGENT

        BaseDefaultDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=DefaultDialogue,
        )
