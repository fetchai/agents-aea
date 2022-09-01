# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""This module contains the tests of the protocols base module."""

import os
import shutil
import tempfile
from copy import copy
from enum import Enum
from pathlib import Path
from typing import Callable, List, Tuple, Type
from unittest.mock import Mock

import pytest
from google.protobuf.struct_pb2 import Struct

from aea.exceptions import AEAEnforceError
from aea.mail.base import Envelope
from aea.mail.base_pb2 import DialogueMessage as Pb2DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage
from aea.protocols.base import Message, Protocol, Serializer
from aea.protocols.dialogue.base import Dialogue, DialogueLabel
from aea.test_tools.constants import UNKNOWN_PROTOCOL_PUBLIC_ID

from packages.fetchai.protocols.default.dialogues import (
    DefaultDialogue,
    DefaultDialogues,
)
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.state_update.dialogues import (
    StateUpdateDialogue,
    StateUpdateDialogues,
)
from packages.open_aea.protocols.signing.dialogues import (
    SigningDialogue,
    SigningDialogues,
)

from tests.conftest import ROOT_DIR


def role_from_first_message_dd(
    message: Message, receiver_address: str
) -> Dialogue.Role:
    """Role from first message."""
    return DefaultDialogue.Role.AGENT


def role_from_first_message_sd(
    message: Message, receiver_address: str
) -> Dialogue.Role:
    """Role from first message."""
    return SigningDialogue.Role.SKILL


def role_from_first_message_sud(
    message: Message, receiver_address: str
) -> Dialogue.Role:
    """Role from first message."""
    return StateUpdateDialogue.Role.SKILL


DIALOGUE_CLASSES: List[Tuple[Type, Type, Enum, Callable]] = [
    (
        DefaultDialogue,
        DefaultDialogues,
        DefaultDialogue.Role.AGENT,
        role_from_first_message_dd,
    ),
    (
        SigningDialogue,
        SigningDialogues,
        SigningDialogue.Role.SKILL,
        role_from_first_message_sd,
    ),
    (
        StateUpdateDialogue,
        StateUpdateDialogues,
        StateUpdateDialogue.Role.SKILL,
        role_from_first_message_sud,
    ),
]


class TMessage(Message):
    """Message class for tests."""

    class _SlotsCls:
        __slots__ = (
            "body_1",
            "body_2",
            "kwarg",
            "content",
            "performative",
            "dialogue_reference",
            "message_id",
            "target",
        )


class TestMessageProperties:
    """Test that the base serializations work."""

    @classmethod
    def setup_class(cls):
        """Setup test."""
        cls.body = {"body_1": "1", "body_2": "2"}
        cls.kwarg = 1
        cls.message = TMessage(cls.body, kwarg=cls.kwarg)

    def test_message_properties(self):
        """Test message properties."""
        for key, value in self.body.items():
            assert self.message.get(key) == value
        assert self.message.get("kwarg") == self.kwarg
        assert not self.message.has_sender
        assert not self.message.has_to
        to = "to"
        sender = "sender"
        self.message.to = to
        self.message.sender = sender
        assert self.message.sender == sender
        assert self.message.to == to
        assert (
            str(self.message)
            == "Message(sender=sender,to=to,body_1=1,body_2=2,kwarg=1)"
        )
        assert (
            repr(self.message)
            == "Message(sender=sender,to=to,body_1=1,body_2=2,kwarg=1)"
        )
        assert self.message.valid_performatives == set()


class ExampleProtobufSerializer(Serializer):
    """
    Example Protobuf serializer.

    It assumes that the Message contains a JSON-serializable body.
    """

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a message into bytes using Protobuf.

        - if one of message_id, target and dialogue_reference are not defined,
          serialize only the message body/
        - otherwise, extract those fields from the body and instantiate
          a Message struct.
        """
        message_pb = ProtobufMessage()
        if msg.has_dialogue_info:
            dialogue_message_pb = Pb2DialogueMessage()
            dialogue_message_pb.message_id = msg.message_id
            dialogue_message_pb.dialogue_starter_reference = msg.dialogue_reference[0]
            dialogue_message_pb.dialogue_responder_reference = msg.dialogue_reference[1]
            dialogue_message_pb.target = msg.target

            new_body = copy(msg._body)  # pylint: disable=protected-access
            new_body.pop("message_id")
            new_body.pop("dialogue_reference")
            new_body.pop("target")

            body_json = Struct()
            body_json.update(new_body)  # pylint: disable=no-member

            dialogue_message_pb.content = (  # pylint: disable=no-member
                body_json.SerializeToString()
            )
            message_pb.dialogue_message.CopyFrom(  # pylint: disable=no-member
                dialogue_message_pb
            )
        else:
            body_json = Struct()
            body_json.update(msg._body)  # pylint: disable=no-member,protected-access
            message_pb.body.CopyFrom(body_json)  # pylint: disable=no-member

        return message_pb.SerializeToString()

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a message using Protobuf.

        First, try to parse the input as a Protobuf 'Message';
        if it fails, parse the bytes as struct.
        """
        message_pb = ProtobufMessage()
        message_pb.ParseFromString(obj)
        message_type = message_pb.WhichOneof("message")
        if message_type == "body":
            body = dict(message_pb.body)  # pylint: disable=no-member
            msg = TMessage(_body=body)
            return msg
        if message_type == "dialogue_message":
            dialogue_message_pb = (
                message_pb.dialogue_message  # pylint: disable=no-member
            )
            message_id = dialogue_message_pb.message_id
            target = dialogue_message_pb.target
            dialogue_starter_reference = dialogue_message_pb.dialogue_starter_reference
            dialogue_responder_reference = (
                dialogue_message_pb.dialogue_responder_reference
            )
            body_json = Struct()
            body_json.ParseFromString(dialogue_message_pb.content)
            body = dict(body_json)
            body["message_id"] = message_id
            body["target"] = target
            body["dialogue_reference"] = (
                dialogue_starter_reference,
                dialogue_responder_reference,
            )
            return TMessage(_body=body)
        raise ValueError("Message type not recognized.")  # pragma: nocover


class TestBaseSerializations:
    """Test that the base serializations work."""

    @classmethod
    def setup_class(cls):
        """Set up the use case."""
        cls.message = TMessage(content="hello")
        cls.message2 = TMessage(_body={"content": "hello"})
        cls.message3 = TMessage(
            message_id=1,
            target=0,
            dialogue_reference=("", ""),
            _body={"content": "hello"},
        )

    def test_default_protobuf_serialization(self):
        """Test that the default Protobuf serialization works."""
        message_bytes = ExampleProtobufSerializer().encode(self.message)
        envelope = Envelope(
            to="receiver",
            sender="sender",
            protocol_specification_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=message_bytes,
        )
        envelope_bytes = envelope.encode()

        expected_envelope = Envelope.decode(envelope_bytes)
        actual_envelope = envelope
        assert expected_envelope == actual_envelope

        expected_msg = ExampleProtobufSerializer().decode(expected_envelope.message)
        actual_msg = self.message
        assert expected_msg == actual_msg

    def test_default_protobuf_serialization_with_dialogue_info(self):
        """Test that the default Protobuf serialization with dialogue info works."""
        message_bytes = ExampleProtobufSerializer().encode(self.message3)
        envelope = Envelope(
            to="receiver",
            sender="sender",
            protocol_specification_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
            message=message_bytes,
        )
        envelope_bytes = envelope.encode()

        expected_envelope = Envelope.decode(envelope_bytes)
        actual_envelope = envelope
        assert expected_envelope == actual_envelope

        expected_msg = ExampleProtobufSerializer().decode(expected_envelope.message)
        actual_msg = self.message3
        assert expected_msg == actual_msg

    def test_set(self):
        """Test that the set method works."""
        self.message._body = {}  # clean values
        key, value = "content", "temporary_value"
        assert self.message.get(key) is None
        self.message.set(key, value)
        assert self.message.get(key) == value

    def test_set_unset(self):
        """Test that the set method works and is reversible."""
        self.message._body = {}  # clean values
        key, value = "content", "temporary_value"
        assert self.message.get(key) is None
        assert not self.message.is_set(key)
        self.message.set(key, None)
        assert self.message.get(key) is None
        assert not self.message.is_set(key)
        self.message.set(key, value)
        assert self.message.get(key) == value
        self.message.set(key, None)
        assert self.message.get(key) is None
        assert not self.message.is_set(key)

    def test_body_setter(self):
        """Test the body setter."""
        m_dict = {"content": "data"}
        self.message2._body = m_dict
        assert self.message2._body == m_dict


class TestMessageEncode:
    """Test the 'Protocol.from_dir' method."""

    def test_encode(self):
        """Test encode on message."""

        class TTMessage(TMessage):
            """Test class extended."""

            serializer = ExampleProtobufSerializer

        msg = TTMessage({"body_1": "1", "body_2": "2"})
        msg.encode()


class TestProtocolFromDir:
    """Test the 'Protocol.from_dir' method."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        shutil.copytree(Path(ROOT_DIR, "packages"), Path(cls.t, "packages"))
        os.chdir(cls.t)

    def test_protocol_load_positive(self):
        """Test protocol loaded correctly."""
        default_protocol = Protocol.from_dir(
            Path("packages", "fetchai", "protocols", "default")
        )
        assert str(default_protocol.public_id) == str(
            DefaultMessage.protocol_id
        ), "Protocol not loaded correctly."
        assert str(default_protocol.protocol_specification_id) == str(
            DefaultMessage.protocol_specification_id
        ), "Protocol not loaded correctly."
        assert default_protocol.serializer is not None

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestMessageAttributes:
    """Test some message attributes."""

    def test_performative(self):
        """Test message performative."""

        class SomePerformative(Message.Performative):
            value = "value"

        message = Message(performative=SomePerformative.value)
        assert message.performative == SomePerformative.value
        assert str(message.performative) == "value"

    def test_to(self):
        """Test the 'to' attribute getter and setter."""
        message = Message()
        with pytest.raises(ValueError, match="Message's 'To' field must be set."):
            message.to

        message.to = "to"
        assert message.to == "to"

        with pytest.raises(AEAEnforceError, match="To already set."):
            message.to = "to"

    def test_dialogue_reference(self):
        """Test the 'dialogue_reference' attribute."""
        message = Message(dialogue_reference=("x", "y"))
        assert message.dialogue_reference == ("x", "y")

    def test_message_id(self):
        """Test the 'message_id' attribute."""
        message = Message(message_id=1)
        assert message.message_id == 1

    def test_target(self):
        """Test the 'target' attribute."""
        message = Message(target=1)
        assert message.target == 1


@pytest.mark.parametrize("dialogue_classes", DIALOGUE_CLASSES)
def test_dialogue(dialogue_classes):
    """Test dialogue initialization."""
    dialogue_class, _, role, _ = dialogue_classes
    dialogue_class(
        DialogueLabel(("x", "y"), "opponent_addr", "starer_addr"), "agent_address", role
    )


@pytest.mark.parametrize("dialogues_classes", DIALOGUE_CLASSES)
def test_dialogues(dialogues_classes):
    """Test dialogues initialization."""
    dialogue_class, dialogues_class, _, role_from_first_message = dialogues_classes
    dialogues_class("agent_address", role_from_first_message, dialogue_class)


def test_protocol_repr():
    """Test protocol repr."""
    config_mock = Mock()
    config_mock.public_id = UNKNOWN_PROTOCOL_PUBLIC_ID
    protocol = Protocol(config_mock, message_class=Message)
    assert repr(protocol) == f"Protocol({UNKNOWN_PROTOCOL_PUBLIC_ID})"
