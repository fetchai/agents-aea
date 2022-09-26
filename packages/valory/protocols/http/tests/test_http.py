# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""Tests package for the 'valory/http' protocol."""
from abc import abstractmethod
from typing import Callable, Type
from unittest import mock

import pytest
from aea.common import Address
from aea.exceptions import AEAEnforceError
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel

from packages.valory.protocols.http import HttpMessage, message
from packages.valory.protocols.http.dialogues import HttpDialogue, HttpDialogues
from packages.valory.protocols.http.message import (
    _default_logger as http_message_logger,
)


LEDGER_ID = "ethereum"


class BaseTestMessageConstruction:
    """Base class to test message construction for the ABCI protocol."""

    msg_class = HttpMessage

    @abstractmethod
    def build_message(self) -> HttpMessage:
        """Build the message to be used for testing."""

    def test_run(self) -> None:
        """Run the test."""
        msg = self.build_message()
        msg.to = "receiver"
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

        actual_msg = self.msg_class.serializer.decode(actual_envelope.message_bytes)
        actual_msg.to = actual_envelope.to
        actual_msg.sender = actual_envelope.sender
        expected_msg = msg
        assert expected_msg == actual_msg


class TestRequest(BaseTestMessageConstruction):
    """Test message."""

    def build_message(self) -> HttpMessage:
        """Build the message."""
        return HttpMessage(
            performative=HttpMessage.Performative.REQUEST,  # type: ignore
            method="GET",
            url="http://example.com",
            version="",
            headers="",
            body=b"",
        )


class TestResponse(BaseTestMessageConstruction):
    """Test message."""

    def build_message(self) -> HttpMessage:
        """Build the message."""
        return HttpMessage(
            performative=HttpMessage.Performative.RESPONSE,  # type: ignore
            version="",
            status_code=200,
            status_text="OK",
            headers="",
            body=b"",
        )


@mock.patch.object(
    message,
    "enforce",
    side_effect=AEAEnforceError("some error"),
)
def test_incorrect_message(
    mocked_enforce: Callable,  # pylint: disable=unused-argument
) -> None:
    """Test that we raise an exception when the message is incorrect."""
    with mock.patch.object(http_message_logger, "error") as mock_logger:
        HttpMessage(
            performative=HttpMessage.Performative.REQUEST,  # type: ignore
            method="GET",
            url="http://example.com",
            version="",
            headers="",
            body=b"",
        )
        mock_logger.assert_any_call("some error")


def test_performative_string_value() -> None:
    """Test the string valoe of performatives."""

    assert (
        str(HttpMessage.Performative.REQUEST) == "request"
    ), "The str value must be request"


def test_encoding_unknown_performative() -> None:
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = HttpMessage(
        performative=HttpMessage.Performative.REQUEST,  # type: ignore
        method="GET",
        url="http://example.com",
        version="",
        headers="",
        body=b"",
    )
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(HttpMessage.Performative, "__eq__", return_value=False):
            HttpMessage.serializer.encode(msg)


def test_decoding_unknown_performative() -> None:
    """Test that we raise an exception when the performative is unknown during encoding."""
    msg = HttpMessage(
        performative=HttpMessage.Performative.REQUEST,  # type: ignore
        method="GET",
        url="http://example.com",
        version="",
        headers="",
        body=b"",
    )

    encoded_msg = HttpMessage.serializer.encode(msg)
    with pytest.raises(ValueError, match="Performative not valid:"):
        with mock.patch.object(HttpMessage.Performative, "__eq__", return_value=False):
            HttpMessage.serializer.decode(encoded_msg)


class AgentDialogue(HttpDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[HttpMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        HttpDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class AgentDialogues(HttpDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom this dialogue is maintained
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message,  # pylint: disable=redefined-outer-name
            receiver_address: Address,
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return HttpDialogue.Role.CLIENT

        HttpDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=AgentDialogue,
        )


class LedgerDialogue(HttpDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: BaseDialogue.Role,
        message_class: Type[HttpMessage],
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class
        """
        HttpDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class LedgerDialogues(HttpDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom this dialogue is maintained
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message,  # pylint: disable=redefined-outer-name
            receiver_address: Address,
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return HttpDialogue.Role.SERVER

        HttpDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=LedgerDialogue,
        )


class TestDialogues:
    """Tests abci dialogues."""

    agent_addr: str
    ledger_addr: str
    agent_dialogues: AgentDialogues
    ledger_dialogues: LedgerDialogues

    @classmethod
    def setup_class(cls) -> None:
        """Set up the test."""
        cls.agent_addr = "agent address"
        cls.ledger_addr = "ledger address"
        cls.agent_dialogues = AgentDialogues(cls.agent_addr)
        cls.ledger_dialogues = LedgerDialogues(cls.ledger_addr)

    def test_create_self_initiated(self) -> None:
        """Test the self initialisation of a dialogue."""
        result = self.agent_dialogues._create_self_initiated(  # pylint: disable=protected-access
            dialogue_opponent_addr=self.ledger_addr,
            dialogue_reference=(str(0), ""),
            role=HttpDialogue.Role.CLIENT,
        )
        assert isinstance(result, HttpDialogue)
        assert result.role == HttpDialogue.Role.CLIENT, "The role must be agent."

    def test_create_opponent_initiated(self) -> None:
        """Test the opponent initialisation of a dialogue."""
        result = self.agent_dialogues._create_opponent_initiated(  # pylint: disable=protected-access
            dialogue_opponent_addr=self.ledger_addr,
            dialogue_reference=(str(0), ""),
            role=HttpDialogue.Role.CLIENT,
        )
        assert isinstance(result, HttpDialogue)
        assert result.role == HttpDialogue.Role.CLIENT, "The role must be agent."
