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
import time
import unittest.mock

import pytest

import aea
from aea.configurations.base import PublicId
from aea.mail.base import Envelope, EnvelopeContext, ProtobufEnvelopeSerializer, URI
from aea.multiplexer import InBox, Multiplexer, OutBox
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage

from packages.fetchai.connections.local.connection import LocalNode

from tests.conftest import (
    UNKNOWN_PROTOCOL_PUBLIC_ID,
    _make_dummy_connection,
    _make_local_connection,
)


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
    msg = Message(content="hello")
    msg.counterparty = receiver_address
    assert Envelope(
        to=receiver_address,
        sender=agent_address,
        protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
        message=msg,
    ), "Cannot generate a new envelope"

    envelope = Envelope(
        to=receiver_address,
        sender=agent_address,
        protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
        message=msg,
    )

    envelope.to = "ChangedAgent"
    envelope.sender = "ChangedSender"
    envelope.protocol_id = "my_changed_protocol"
    envelope.message = b"HelloWorld"

    assert envelope.to == "ChangedAgent", "Cannot set to value on Envelope"
    assert envelope.sender == "ChangedSender", "Cannot set sender value on Envelope"
    assert (
        envelope.protocol_id == "my_changed_protocol"
    ), "Cannot set protocol_id on Envelope "
    assert envelope.message == b"HelloWorld", "Cannot set message on Envelope"
    assert envelope.context.uri_raw is not None


def test_inbox_empty():
    """Tests if the inbox is empty."""
    multiplexer = Multiplexer([_make_dummy_connection()])
    _inbox = InBox(multiplexer)
    assert _inbox.empty(), "Inbox is not empty"


def test_inbox_nowait():
    """Tests the inbox without waiting."""
    agent_address = "Agent0"
    receiver_address = "Agent1"
    msg = Message(content="hello")
    msg.counterparty = receiver_address
    multiplexer = Multiplexer([_make_dummy_connection()])
    envelope = Envelope(
        to=receiver_address,
        sender=agent_address,
        protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
        message=msg,
    )
    multiplexer.in_queue.put(envelope)
    inbox = InBox(multiplexer)
    assert (
        inbox.get_nowait() == envelope
    ), "Check for a message on the in queue and wait for no time."


def test_inbox_get():
    """Tests for a envelope on the in queue."""
    agent_address = "Agent0"
    receiver_address = "Agent1"
    msg = Message(content="hello")
    msg.counterparty = receiver_address
    multiplexer = Multiplexer([_make_dummy_connection()])
    envelope = Envelope(
        to=receiver_address,
        sender=agent_address,
        protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
        message=msg,
    )
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
    msg.counterparty = receiver_address
    dummy_connection = _make_dummy_connection()
    multiplexer = Multiplexer([dummy_connection])
    outbox = OutBox(multiplexer, agent_address)
    inbox = InBox(multiplexer)
    multiplexer.connect()
    envelope = Envelope(
        to=receiver_address,
        sender=agent_address,
        protocol_id=DefaultMessage.protocol_id,
        message=msg,
    )
    outbox.put(envelope)
    time.sleep(0.5)
    assert not inbox.empty(), "Inbox must not be empty after putting an envelope"
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
    msg.counterparty = receiver_address
    dummy_connection = _make_dummy_connection()
    multiplexer = Multiplexer([dummy_connection])
    outbox = OutBox(multiplexer, agent_address)
    inbox = InBox(multiplexer)
    multiplexer.connect()
    outbox.put_message(msg)
    time.sleep(0.5)
    assert not inbox.empty(), "Inbox will not be empty after putting a message."
    multiplexer.disconnect()


def test_outbox_empty():
    """Test thet the outbox queue is empty."""
    agent_address = "Agent0"
    dummy_connection = _make_dummy_connection()
    multiplexer = Multiplexer([dummy_connection])
    multiplexer.connect()
    outbox = OutBox(multiplexer, agent_address)
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


def test_protobuf_envelope_serializer():
    """Test Protobuf envelope serializer."""
    serializer = ProtobufEnvelopeSerializer()
    # connection id is None because it is not included in the encoded envelope
    envelope_context = EnvelopeContext(connection_id=None, uri=URI("/uri"))
    expected_envelope = Envelope(
        to="to",
        sender="sender",
        protocol_id=PublicId("author", "name", "0.1.0"),
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
        protocol_id=PublicId("author", "name", "0.1.0"),
        message=b"message",
    )
    encoded_envelope = expected_envelope.encode()
    actual_envelope = Envelope.decode(encoded_envelope)

    assert actual_envelope == expected_envelope


def test_envelope_message_bytes():
    """Test the property Envelope.message_bytes."""
    message = DefaultMessage(DefaultMessage.Performative.BYTES, content=b"message")
    envelope = Envelope(
        to="to",
        sender="sender",
        protocol_id=PublicId("author", "name", "0.1.0"),
        message=message,
    )

    expected_message_bytes = message.encode()
    actual_message_bytes = envelope.message_bytes
    assert expected_message_bytes == actual_message_bytes


def test_envelope_skill_id():
    """Test the property Envelope.skill_id."""
    envelope_context = EnvelopeContext(uri=URI("author/skill_name/0.1.0"))
    envelope = Envelope(
        to="to",
        sender="sender",
        protocol_id=PublicId("author", "name", "0.1.0"),
        message=b"message",
        context=envelope_context,
    )

    assert envelope.skill_id == PublicId("author", "skill_name", "0.1.0")


def test_envelope_skill_id_raises_value_error():
    """Test the property Envelope.skill_id raises ValueError if the URI is not a public id.."""
    with unittest.mock.patch.object(
        aea.mail.base.logger, "debug"
    ) as mock_logger_method:
        # with caplog.at_level(logging.DEBUG, logger="aea.mail.base"):
        bad_uri = "author/skill_name/bad_version"
        envelope_context = EnvelopeContext(uri=URI(bad_uri))
        envelope = Envelope(
            to="to",
            sender="sender",
            protocol_id=PublicId("author", "name", "0.1.0"),
            message=b"message",
            context=envelope_context,
        )

        assert envelope.skill_id is None
        # assert (
        #     f"URI - {bad_uri} - not a valid skill id." in caplog.text
        # ), f"Cannot find message in output: {caplog.text}"
        mock_logger_method.assert_called_with(
            f"URI - {bad_uri} - not a valid skill id."
        )
