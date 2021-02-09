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
"""This module contains the tests for Envelope of mail.base.py."""
import unittest.mock

import pytest

import aea
from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError
from aea.mail import base_pb2
from aea.mail.base import Envelope, EnvelopeContext, ProtobufEnvelopeSerializer, URI
from aea.multiplexer import InBox, Multiplexer, OutBox
from aea.protocols.base import Message

from packages.fetchai.connections.local.connection import LocalNode
from packages.fetchai.protocols.default.message import DefaultMessage

from tests.common.utils import wait_for_condition
from tests.conftest import _make_dummy_connection, _make_local_connection


def test_uri():
    """Testing the uri initialisation."""
    uri_raw = "http://user:pwd@NetLoc:80/path;param?query=arg#frag"
    uri = URI(uri_raw=uri_raw)
    assert uri_raw == str(uri)
    assert uri.scheme == "http"
    assert uri.netloc == "user:pwd@NetLoc:80"
    assert uri.path == "/path"
    assert uri.params == "param"
    assert uri.query == "query=arg"
    assert uri.fragment == "frag"
    assert uri.host == "netloc"
    assert uri.port == 80
    assert uri.username == "user"
    assert uri.password == "pwd"


def test_uri_eq():
    """Testing the uri __eq__ function."""
    uri_raw = "http://user:pwd@NetLoc:80/path;param?query=arg#frag"
    uri = URI(uri_raw=uri_raw)
    assert uri == uri


def test_envelope_initialisation():
    """Testing the envelope initialisation."""
    agent_address = "Agent0"
    receiver_address = "Agent1"
    msg = DefaultMessage(
        performative=DefaultMessage.Performative.BYTES, content="hello"
    )
    msg.to = receiver_address

    envelope = Envelope(to=receiver_address, sender=agent_address, message=msg,)

    assert envelope, "Cannot generate a new envelope"

    envelope.to = "ChangedAgent"
    envelope.sender = "ChangedSender"
    envelope.message = b"HelloWorld"

    assert envelope.to == "ChangedAgent", "Cannot set to value on Envelope"
    assert envelope.sender == "ChangedSender", "Cannot set sender value on Envelope"
    assert envelope.message == b"HelloWorld", "Cannot set message on Envelope"
    assert envelope.context.uri_raw is not None
    assert not envelope.is_sender_public_id
    assert not envelope.is_to_public_id


def test_inbox_empty():
    """Tests if the inbox is empty."""
    multiplexer = Multiplexer([_make_dummy_connection()])
    _inbox = InBox(multiplexer)
    assert _inbox.empty(), "Inbox is not empty"


def test_inbox_nowait():
    """Tests the inbox without waiting."""
    agent_address = "Agent0"
    receiver_address = "Agent1"
    msg = DefaultMessage(
        performative=DefaultMessage.Performative.BYTES, content="hello"
    )
    msg.to = receiver_address
    multiplexer = Multiplexer([_make_dummy_connection()])
    envelope = Envelope(to=receiver_address, sender=agent_address, message=msg,)
    multiplexer.in_queue.put(envelope)
    inbox = InBox(multiplexer)
    assert (
        inbox.get_nowait() == envelope
    ), "Check for a message on the in queue and wait for no time."


def test_inbox_get():
    """Tests for a envelope on the in queue."""
    agent_address = "Agent0"
    receiver_address = "Agent1"
    msg = DefaultMessage(
        performative=DefaultMessage.Performative.BYTES, content="hello"
    )
    msg.to = receiver_address
    multiplexer = Multiplexer([_make_dummy_connection()])
    envelope = Envelope(to=receiver_address, sender=agent_address, message=msg,)
    multiplexer.in_queue.put(envelope)
    inbox = InBox(multiplexer)

    assert (
        inbox.get() == envelope
    ), "Checks if the returned envelope is the same with the queued envelope."


def test_inbox_get_raises_exception_when_empty():
    """Test that getting an envelope from an empty inbox raises an exception."""
    multiplexer = Multiplexer([_make_dummy_connection()])
    inbox = InBox(multiplexer)

    with pytest.raises(aea.mail.base.Empty):
        with unittest.mock.patch.object(multiplexer, "get", return_value=None):
            inbox.get()


def test_inbox_get_nowait_returns_none():
    """Test that getting an envelope from an empty inbox returns None."""
    # TODO get_nowait in this case should raise an exception, like it's done in queue.Queue
    multiplexer = Multiplexer([_make_dummy_connection()])
    inbox = InBox(multiplexer)
    assert inbox.get_nowait() is None


def test_outbox_put():
    """Tests that an envelope is putted into the queue."""
    agent_address = "Agent0"
    receiver_address = "Agent1"
    msg = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"hello",
    )
    msg.to = receiver_address
    msg.sender = agent_address
    dummy_connection = _make_dummy_connection()
    multiplexer = Multiplexer([dummy_connection])
    outbox = OutBox(multiplexer)
    inbox = InBox(multiplexer)
    multiplexer.connect()
    envelope = Envelope(to=receiver_address, sender=agent_address, message=msg,)
    outbox.put(envelope)
    wait_for_condition(
        lambda: inbox.empty(), 15, "Inbox must not be empty after putting an envelope"
    )
    multiplexer.disconnect()


def test_outbox_put_message():
    """Tests that an envelope is created from the message is in the queue."""
    agent_address = "Agent0"
    receiver_address = "Agent1"
    msg = DefaultMessage(
        dialogue_reference=("", ""),
        message_id=1,
        target=0,
        performative=DefaultMessage.Performative.BYTES,
        content=b"hello",
    )
    msg.to = receiver_address
    msg.sender = agent_address
    dummy_connection = _make_dummy_connection()
    multiplexer = Multiplexer([dummy_connection])
    outbox = OutBox(multiplexer)
    inbox = InBox(multiplexer)
    multiplexer.connect()
    wait_for_condition(
        lambda: multiplexer.is_connected, 15, "Multiplexer is not connected"
    )
    outbox.put_message(msg)
    wait_for_condition(
        lambda: inbox.empty(), 15, "Inbox must not be empty after putting a message"
    )
    multiplexer.disconnect()


def test_outbox_empty():
    """Test thet the outbox queue is empty."""
    dummy_connection = _make_dummy_connection()
    multiplexer = Multiplexer([dummy_connection])
    multiplexer.connect()
    outbox = OutBox(multiplexer)
    assert outbox.empty(), "The outbox is not empty"
    multiplexer.disconnect()


def test_multiplexer():
    """Tests if the multiplexer is connected."""
    with LocalNode() as node:
        address_1 = "address_1"
        oef_local_connection = _make_local_connection(address_1, node)
        multiplexer = Multiplexer([oef_local_connection])
        multiplexer.connect()
        assert (
            multiplexer.is_connected
        ), "Mailbox cannot connect to the specific Connection(OEFLocalConnection)"
        multiplexer.disconnect()


def test_envelope_fails_on_message_empty_protocol_specification_id():
    """Check message.protocol_specification_id."""

    class BadMessage(Message):
        protocol_id = "some/some:0.1.0"

    message = BadMessage()

    with pytest.raises(ValueError):
        Envelope(message=message, to="1", sender="1")


def test_protobuf_envelope_serializer():
    """Test Protobuf envelope serializer."""
    serializer = ProtobufEnvelopeSerializer()
    # connection id is None because it is not included in the encoded envelope
    envelope_context = EnvelopeContext(connection_id=None, uri=URI("/uri"))
    expected_envelope = Envelope(
        to="to",
        sender="sender",
        protocol_specification_id=PublicId("author", "name", "0.1.0"),
        message=b"message",
        context=envelope_context,
    )
    encoded_envelope = serializer.encode(expected_envelope)
    actual_envelope = serializer.decode(encoded_envelope)

    assert actual_envelope == expected_envelope


def test_envelope_serialization():
    """Test Envelope.encode and Envelope.decode methods."""
    expected_envelope = Envelope(
        to="to",
        sender="sender",
        protocol_specification_id=PublicId("author", "name", "0.1.0"),
        message=b"message",
    )
    encoded_envelope = expected_envelope.encode()
    actual_envelope = Envelope.decode(encoded_envelope)

    assert actual_envelope == expected_envelope


def test_envelope_message_bytes():
    """Test the property Envelope.message_bytes."""
    message = DefaultMessage(DefaultMessage.Performative.BYTES, content=b"message")
    envelope = Envelope(to="to", sender="sender", message=message,)

    expected_message_bytes = message.encode()
    actual_message_bytes = envelope.message_bytes
    assert expected_message_bytes == actual_message_bytes


def test_envelope_skill_id():
    """Test the property Envelope.skill_id."""
    envelope_context = EnvelopeContext(uri=URI("skill/author/skill_name/0.1.0"))
    envelope = Envelope(
        to="to",
        sender="sender",
        protocol_specification_id=PublicId("author", "name", "0.1.0"),
        message=b"message",
        context=envelope_context,
    )

    assert envelope.skill_id == PublicId("author", "skill_name", "0.1.0")


def test_envelope_connection_id():
    """Test the property Envelope.connection_id."""
    envelope_context = EnvelopeContext(
        uri=URI("connection/author/connection_name/0.1.0")
    )
    envelope = Envelope(
        to="to",
        sender="sender",
        protocol_specification_id=PublicId("author", "name", "0.1.0"),
        message=b"message",
        context=envelope_context,
    )

    assert envelope.connection_id == PublicId("author", "connection_name", "0.1.0")


def test_envelope_skill_id_raises_value_error():
    """Test the property Envelope.skill_id raises ValueError if the URI is not a package id.."""
    with unittest.mock.patch.object(
        aea.mail.base._default_logger, "debug"
    ) as mock_logger_method:
        bad_uri = "skill/author/skill_name/bad_version"
        envelope_context = EnvelopeContext(uri=URI(bad_uri))
        envelope = Envelope(
            to="to",
            sender="sender",
            protocol_specification_id=PublicId("author", "name", "0.1.0"),
            message=b"message",
            context=envelope_context,
        )

        assert envelope.skill_id is None
        mock_logger_method.assert_called_with(
            f"URI - {bad_uri} - not a valid package_id id. Error: Input '{bad_uri}' is not well formatted."
        )


def test_envelope_skill_id_raises_value_error_wrong_package_type():
    """Test the property Envelope.skill_id raises ValueError if the URI is not a valid package type."""
    with unittest.mock.patch.object(
        aea.mail.base._default_logger, "debug"
    ) as mock_logger_method:
        invalid_uri = "protocol/author/skill_name/0.1.0"
        envelope_context = EnvelopeContext(uri=URI(invalid_uri))
        envelope = Envelope(
            to="to",
            sender="sender",
            protocol_specification_id=PublicId("author", "name", "0.1.0"),
            message=b"message",
            context=envelope_context,
        )

        assert envelope.skill_id is None
        mock_logger_method.assert_called_with(
            f"URI - {invalid_uri} - not a valid package_id id. Error: Invalid package type protocol in uri for envelope context."
        )


def test_envelope_context_raises_with_public_id_specified_twice():
    """Test the EnvelopeContext constructor, negative"""
    with pytest.raises(
        ValueError, match="Cannot define connection_id explicitly and in URI."
    ):
        EnvelopeContext(
            uri=URI("connection/author/connection_name/0.1.0"),
            connection_id=PublicId("author", "connection_name", "0.1.0"),
        )
    with pytest.raises(
        ValueError, match="Cannot define skill_id explicitly and in URI."
    ):
        EnvelopeContext(
            uri=URI("skill/author/skill_name/0.1.0"),
            skill_id=PublicId("author", "skill_name", "0.1.0"),
        )


def test_envelope_constructor():
    """Test Envelope constructor checks."""
    Envelope(
        to="to",
        sender="sender",
        message=DefaultMessage(performative=DefaultMessage.Performative.BYTES),
    )
    Envelope(
        to="to",
        sender="sender",
        message=b"",
        protocol_specification_id=DefaultMessage.protocol_specification_id,
    )

    with pytest.raises(
        AEAEnforceError, match="message should be a type of Message or bytes!"
    ):
        Envelope(to="to", sender="sender", message=123)

    with pytest.raises(
        Exception,
        match=r"Message is bytes object, protocol_specification_id must be provided!",
    ):
        Envelope(to="asd", sender="asdasd", message=b"sdfdf")


def test_envelope_context_repr():
    """Check repr for EnvelopeContext."""
    assert (
        str(EnvelopeContext(1, 2))
        == "EnvelopeContext(connection_id=1, skill_id=2, uri_raw=)"
    )


def test_envelope_specification_id_translated():
    """Test protocol id to protocol specification id translation and back."""
    protocol_specification_id = PublicId("author", "specification", "0.1.0")

    envelope = Envelope(
        to="to",
        sender="sender",
        protocol_specification_id=protocol_specification_id,
        message=b"",
    )

    assert envelope.protocol_specification_id == protocol_specification_id

    envelope_bytes = envelope.encode()
    envelope_pb = base_pb2.Envelope()
    envelope_pb.ParseFromString(envelope_bytes)

    new_envelope = Envelope.decode(envelope_bytes)
    assert new_envelope.protocol_specification_id == envelope.protocol_specification_id
