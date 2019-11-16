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

"""This module contains the tests of the local OEF node implementation."""
import asyncio
import unittest.mock

import pytest

from aea.connections.base import AEAConnectionError
from aea.connections.local.connection import LocalNode, OEFLocalConnection
from aea.mail.base import Envelope, MailBox
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer


def test_connection():
    """Test that two mailbox can connect to the node."""
    node = LocalNode()

    mailbox1 = MailBox([OEFLocalConnection("mailbox1", node)])
    mailbox2 = MailBox([OEFLocalConnection("mailbox2", node)])

    mailbox1.connect()
    mailbox2.connect()

    mailbox1.disconnect()
    mailbox2.disconnect()


@pytest.mark.asyncio
async def test_connection_twice_return_none():
    """Test that connecting twice works."""
    with LocalNode() as node:
        public_key = "mailbox"
        connection = OEFLocalConnection(public_key, node)
        await connection.connect()
        await node.connect(public_key, connection._reader)
        message = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        message_bytes = DefaultSerializer().encode(message)
        expected_envelope = Envelope(to=public_key, sender=public_key, protocol_id="default", message=message_bytes)
        await connection.send(expected_envelope)
        actual_envelope = await connection.recv()

        assert expected_envelope == actual_envelope

        await connection.disconnect()


@pytest.mark.asyncio
async def test_receiving_when_not_connected_raise_exception():
    """Test that when we try to receive an envelope from a not connected connection we raise exception."""
    with pytest.raises(AEAConnectionError, match="Connection not established yet."):
        with LocalNode() as node:
            public_key = "mailbox"
            connection = OEFLocalConnection(public_key, node)
            await connection.recv()


@pytest.mark.asyncio
async def test_receiving_returns_none_when_error_occurs():
    """Test that when we try to receive an envelope and an error occurs we return None."""
    with LocalNode() as node:
        public_key = "mailbox"
        connection = OEFLocalConnection(public_key, node)
        await connection.connect()

        with unittest.mock.patch.object(connection._reader, "get", side_effect=Exception):
            result = await connection.recv()
            assert result is None

        await connection.disconnect()


def test_communication():
    """Test that two mailbox can communicate through the node."""
    with LocalNode() as node:

        mailbox1 = MailBox([OEFLocalConnection("mailbox1", node)])
        mailbox2 = MailBox([OEFLocalConnection("mailbox2", node)])

        mailbox1.connect()
        mailbox2.connect()

        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        msg_bytes = DefaultSerializer().encode(msg)
        envelope = Envelope(to="mailbox2", sender="mailbox1", protocol_id=DefaultMessage.protocol_id, message=msg_bytes)
        mailbox1.send(envelope)

        msg = FIPAMessage(0, 0, 0, FIPAMessage.Performative.CFP, query=None)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to="mailbox2", sender="mailbox1", protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        mailbox1.send(envelope)

        msg = FIPAMessage(0, 0, 0, FIPAMessage.Performative.PROPOSE, proposal=[])
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to="mailbox2", sender="mailbox1", protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        mailbox1.send(envelope)

        msg = FIPAMessage(0, 0, 0, FIPAMessage.Performative.ACCEPT)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to="mailbox2", sender="mailbox1", protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        mailbox1.send(envelope)

        msg = FIPAMessage(0, 0, 0, FIPAMessage.Performative.DECLINE)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(to="mailbox2", sender="mailbox1", protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        mailbox1.send(envelope)

        envelope = mailbox2.inbox.get(block=True, timeout=1.0)
        msg = DefaultSerializer().decode(envelope.message)
        assert envelope.protocol_id == "default"
        assert msg.get("content") == b"hello"
        envelope = mailbox2.inbox.get(block=True, timeout=1.0)
        msg = FIPASerializer().decode(envelope.message)
        assert envelope.protocol_id == "fipa"
        assert msg.get("performative") == FIPAMessage.Performative.CFP
        envelope = mailbox2.inbox.get(block=True, timeout=1.0)
        msg = FIPASerializer().decode(envelope.message)
        assert envelope.protocol_id == "fipa"
        assert msg.get("performative") == FIPAMessage.Performative.PROPOSE
        envelope = mailbox2.inbox.get(block=True, timeout=1.0)
        msg = FIPASerializer().decode(envelope.message)
        assert envelope.protocol_id == "fipa"
        assert msg.get("performative") == FIPAMessage.Performative.ACCEPT
        envelope = mailbox2.inbox.get(block=True, timeout=1.0)
        msg = FIPASerializer().decode(envelope.message)
        assert envelope.protocol_id == "fipa"
        assert msg.get("performative") == FIPAMessage.Performative.DECLINE
        mailbox1.disconnect()
        mailbox2.disconnect()


@pytest.mark.asyncio
async def test_connecting_to_node_with_same_key():
    """Test that connecting twice with the same key works correctly."""
    node = LocalNode()
    public_key = "my_public_key"
    my_queue = asyncio.Queue()

    ret = await node.connect(public_key, my_queue)
    assert ret is not None and isinstance(ret, asyncio.Queue)
    ret = await node.connect(public_key, my_queue)
    assert ret is None
