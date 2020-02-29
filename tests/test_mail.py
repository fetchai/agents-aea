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
from aea.mail.base import Envelope, InBox, Multiplexer, OutBox, URI
from aea.protocols.base import Message
from aea.protocols.base import ProtobufSerializer
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer

from packages.fetchai.connections.local.connection import LocalNode, OEFLocalConnection

from .conftest import (
    DUMMY_CONNECTION_PUBLIC_ID,
    DummyConnection,
    UNKNOWN_PROTOCOL_PUBLIC_ID,
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
    msg = Message(content="hello")
    message_bytes = ProtobufSerializer().encode(msg)
    assert Envelope(
        to="Agent1",
        sender="Agent0",
        protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
        message=message_bytes,
    ), "Cannot generate a new envelope"

    envelope = Envelope(
        to="Agent1",
        sender="Agent0",
        protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
        message=message_bytes,
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
    multiplexer = Multiplexer(
        [DummyConnection(connection_id=DUMMY_CONNECTION_PUBLIC_ID)]
    )
    _inbox = InBox(multiplexer)
    assert _inbox.empty(), "Inbox is not empty"


def test_inbox_nowait():
    """Tests the inbox without waiting."""
    msg = Message(content="hello")
    message_bytes = ProtobufSerializer().encode(msg)
    multiplexer = Multiplexer(
        [DummyConnection(connection_id=DUMMY_CONNECTION_PUBLIC_ID)]
    )
    envelope = Envelope(
        to="Agent1",
        sender="Agent0",
        protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
        message=message_bytes,
    )
    multiplexer.in_queue.put(envelope)
    inbox = InBox(multiplexer)
    assert (
        inbox.get_nowait() == envelope
    ), "Check for a message on the in queue and wait for no time."


def test_inbox_get():
    """Tests for a envelope on the in queue."""
    msg = Message(content="hello")
    message_bytes = ProtobufSerializer().encode(msg)
    multiplexer = Multiplexer(
        [DummyConnection(connection_id=DUMMY_CONNECTION_PUBLIC_ID)]
    )
    envelope = Envelope(
        to="Agent1",
        sender="Agent0",
        protocol_id=UNKNOWN_PROTOCOL_PUBLIC_ID,
        message=message_bytes,
    )
    multiplexer.in_queue.put(envelope)
    inbox = InBox(multiplexer)

    assert (
        inbox.get() == envelope
    ), "Checks if the returned envelope is the same with the queued envelope."


def test_inbox_get_raises_exception_when_empty():
    """Test that getting an envelope from an empty inbox raises an exception."""
    multiplexer = Multiplexer(
        [DummyConnection(connection_id=DUMMY_CONNECTION_PUBLIC_ID)]
    )
    inbox = InBox(multiplexer)

    with pytest.raises(aea.mail.base.Empty):
        with unittest.mock.patch.object(multiplexer, "get", return_value=None):
            inbox.get()


def test_inbox_get_nowait_returns_none():
    """Test that getting an envelope from an empty inbox returns None."""
    # TODO get_nowait in this case should raise an exception, like it's done in queue.Queue
    multiplexer = Multiplexer(
        [DummyConnection(connection_id=DUMMY_CONNECTION_PUBLIC_ID)]
    )
    inbox = InBox(multiplexer)
    assert inbox.get_nowait() is None


def test_outbox_put():
    """Tests that an envelope is putted into the queue."""
    msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
    message_bytes = DefaultSerializer().encode(msg)
    multiplexer = Multiplexer(
        [DummyConnection(connection_id=DUMMY_CONNECTION_PUBLIC_ID)]
    )
    outbox = OutBox(multiplexer)
    inbox = InBox(multiplexer)
    multiplexer.connect()
    envelope = Envelope(
        to="Agent1",
        sender="Agent0",
        protocol_id=DefaultMessage.protocol_id,
        message=message_bytes,
    )
    outbox.put(envelope)
    time.sleep(0.5)
    assert not inbox.empty(), "Inbox must not be empty after putting an envelope"
    multiplexer.disconnect()


def test_outbox_put_message():
    """Tests that an envelope is created from the message is in the queue."""
    msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
    message_bytes = DefaultSerializer().encode(msg)
    multiplexer = Multiplexer(
        [DummyConnection(connection_id=DUMMY_CONNECTION_PUBLIC_ID)]
    )
    outbox = OutBox(multiplexer)
    inbox = InBox(multiplexer)
    multiplexer.connect()
    outbox.put_message("Agent1", "Agent0", DefaultMessage.protocol_id, message_bytes)
    time.sleep(0.5)
    assert not inbox.empty(), "Inbox will not be empty after putting a message."
    multiplexer.disconnect()


def test_outbox_empty():
    """Test thet the outbox queue is empty."""
    multiplexer = Multiplexer(
        [DummyConnection(connection_id=DUMMY_CONNECTION_PUBLIC_ID)]
    )
    multiplexer.connect()
    outbox = OutBox(multiplexer)
    assert outbox.empty(), "The outbox is not empty"
    multiplexer.disconnect()


def test_multiplexer():
    """Tests if the multiplexer is connected."""
    with LocalNode() as node:
        address_1 = "address_1"
        multiplexer = Multiplexer(
            [
                OEFLocalConnection(
                    address_1, node, connection_id=PublicId("fetchai", "local", "0.1.0")
                )
            ]
        )
        multiplexer.connect()
        assert (
            multiplexer.is_connected
        ), "Mailbox cannot connect to the specific Connection(OEFLocalConnection)"
        multiplexer.disconnect()
