# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022-2023 Valory AG
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
"""This module contains test case classes based on pytest for AEA protocol testing."""


from abc import ABC, abstractmethod
from typing import List, Type
from unittest.mock import patch

import pytest

from aea.common import Address
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, Dialogues


class BaseProtocolMessagesTestCase(ABC):
    """Base class to test messages for the protocol."""

    @property
    @abstractmethod
    def MESSAGE_CLASS(self) -> Type[Message]:
        """Override this property in a subclass."""

    def perform_message_test(self, msg: Message) -> None:  # nosec
        """Test message encode/decode."""
        msg.to = "receiver"
        assert msg._is_consistent()  # pylint: disable=protected-access
        envelope = Envelope(to=msg.to, sender="sender", message=msg)
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

        actual_msg = self.MESSAGE_CLASS.serializer.decode(actual_envelope.message_bytes)
        actual_msg.to = actual_envelope.to
        actual_msg.sender = actual_envelope.sender
        expected_msg = msg
        assert expected_msg == actual_msg

    def test_messages_ok(self) -> None:
        """Run messages are ok for encode and decode."""
        for msg in self.build_messages():
            self.perform_message_test(msg)

    def test_messages_inconsistent(self) -> None:
        """Run messages are inconsistent."""
        for msg in self.build_inconsistent():
            assert (  # nosec
                not msg._is_consistent()  # pylint: disable=protected-access
            ), msg

    def test_messages_fail_to_encode_decode(self) -> None:
        """Run messages are failing to encode and decode."""
        msg = self.build_messages()[0]
        with patch.object(msg.__class__.Performative, "__eq__", return_value=False):
            with pytest.raises(
                ValueError, match=f"Performative not valid: {msg.performative}"
            ):
                msg.serializer.encode(msg)

        encoded_msg = msg.serializer.encode(msg)
        with patch.object(msg.__class__.Performative, "__eq__", return_value=False):
            with pytest.raises(
                ValueError, match=f"Performative not valid: {msg.performative}"
            ):
                msg.serializer.decode(encoded_msg)

    @abstractmethod
    def build_messages(self) -> List[Message]:  # type: ignore[override]
        """Build the messages to be used for testing."""

    @abstractmethod
    def build_inconsistent(self) -> List[Message]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""


class BaseProtocolDialoguesTestCase(ABC):
    """Base class to test message construction for the protocol."""

    @property
    @abstractmethod
    def MESSAGE_CLASS(self) -> Type[Message]:
        """Override this property in a subclass."""

    @property
    @abstractmethod
    def DIALOGUE_CLASS(self) -> Type[Dialogue]:
        """Override this property in a subclass."""

    @property
    @abstractmethod
    def DIALOGUES_CLASS(self) -> Type[Dialogues]:
        """Override this property in a subclass."""

    @property
    @abstractmethod
    def ROLE_FOR_THE_FIRST_MESSAGE(self) -> Dialogue.Role:
        """Override this property in a subclass."""

    def role_from_first_message(  # pylint: disable=unused-argument
        self,
        message: Message,
        receiver_address: Address,
    ) -> Dialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :param receiver_address: the address of the receiving agent
        :return: The role of the agent
        """
        return self.ROLE_FOR_THE_FIRST_MESSAGE

    def make_dialogues_class(self) -> Type[Dialogues]:
        """Make dialogues class with specific role."""

        def new_init(self_: Dialogues, self_address: Address) -> None:
            """New init function."""
            self.DIALOGUES_CLASS.__init__(  # type: ignore # pylint: disable=no-value-for-parameter
                self_,
                self_address=self_address,
                role_from_first_message=self.role_from_first_message,
                dialogue_class=self.DIALOGUE_CLASS,
            )

        return type(
            f"ForTest{self.DIALOGUES_CLASS.__name__}",
            (self.DIALOGUES_CLASS,),
            {"__init__": new_init},
        )

    @abstractmethod
    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""

    def test_dialogues(self) -> None:
        """Test dialogues."""
        dialogues_class = self.make_dialogues_class()
        dialogues = dialogues_class("agent_addr")  # type: ignore
        _, dialogue = dialogues.create(
            counterparty="some", **self.make_message_content()
        )
        assert dialogue is not None  # nosec
