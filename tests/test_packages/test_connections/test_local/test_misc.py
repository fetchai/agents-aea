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

from aea.mail.base import AEAConnectionError, Envelope, Multiplexer
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer

from packages.fetchai.connections.local.connection import LocalNode, OEFLocalConnection
from packages.fetchai.protocols.fipa.message import FIPAMessage
from packages.fetchai.protocols.fipa.serialization import FIPASerializer


def test_connection():
    """Test that two OEF local connection can connect to a local node."""
    with LocalNode() as node:

        multiplexer1 = Multiplexer([OEFLocalConnection("multiplexer1", node)])
        multiplexer2 = Multiplexer([OEFLocalConnection("multiplexer2", node)])

        multiplexer1.connect()
        multiplexer2.connect()

        multiplexer1.disconnect()
        multiplexer2.disconnect()


@pytest.mark.asyncio
async def test_connection_twice_return_none():
    """Test that connecting twice works."""
    with LocalNode() as node:
        address = "address"
        connection = OEFLocalConnection(address, node)
        await connection.connect()
        await node.connect(address, connection._reader)
        message = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        message_bytes = DefaultSerializer().encode(message)
        expected_envelope = Envelope(
            to=address, sender=address, protocol_id="default", message=message_bytes
        )
        await connection.send(expected_envelope)
        actual_envelope = await connection.receive()

        assert expected_envelope == actual_envelope

        await connection.disconnect()


@pytest.mark.asyncio
async def test_receiving_when_not_connected_raise_exception():
    """Test that when we try to receive an envelope from a not connected connection we raise exception."""
    with pytest.raises(AEAConnectionError, match="Connection not established yet."):
        with LocalNode() as node:
            address = "address"
            connection = OEFLocalConnection(address, node)
            await connection.receive()


@pytest.mark.asyncio
async def test_receiving_returns_none_when_error_occurs():
    """Test that when we try to receive an envelope and an error occurs we return None."""
    with LocalNode() as node:
        address = "address"
        connection = OEFLocalConnection(address, node)
        await connection.connect()

        with unittest.mock.patch.object(
            connection._reader, "get", side_effect=Exception
        ):
            result = await connection.receive()
            assert result is None

        await connection.disconnect()


def test_communication():
    """Test that two multiplexer can communicate through the node."""
    with LocalNode() as node:

        multiplexer1 = Multiplexer([OEFLocalConnection("multiplexer1", node)])
        multiplexer2 = Multiplexer([OEFLocalConnection("multiplexer2", node)])

        multiplexer1.connect()
        multiplexer2.connect()

        msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b"hello")
        msg_bytes = DefaultSerializer().encode(msg)
        envelope = Envelope(
            to="multiplexer2",
            sender="multiplexer1",
            protocol_id=DefaultMessage.protocol_id,
            message=msg_bytes,
        )
        multiplexer1.put(envelope)

        msg = FIPAMessage((str(0), ""), 0, 0, FIPAMessage.Performative.CFP, query=None)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(
            to="multiplexer2",
            sender="multiplexer1",
            protocol_id=FIPAMessage.protocol_id,
            message=msg_bytes,
        )
        multiplexer1.put(envelope)

        msg = FIPAMessage(
            (str(0), str(1)),
            0,
            0,
            FIPAMessage.Performative.PROPOSE,
            proposal=[],
        )
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(
            to="multiplexer2",
            sender="multiplexer1",
            protocol_id=FIPAMessage.protocol_id,
            message=msg_bytes,
        )
        multiplexer1.put(envelope)

        msg = FIPAMessage((str(0), str(1)), 0, 0, FIPAMessage.Performative.ACCEPT)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(
            to="multiplexer2",
            sender="multiplexer1",
            protocol_id=FIPAMessage.protocol_id,
            message=msg_bytes,
        )
        multiplexer1.put(envelope)

        msg = FIPAMessage((str(0), str(1)), 0, 0, FIPAMessage.Performative.DECLINE)
        msg_bytes = FIPASerializer().encode(msg)
        envelope = Envelope(
            to="multiplexer2",
            sender="multiplexer1",
            protocol_id=FIPAMessage.protocol_id,
            message=msg_bytes,
        )
        multiplexer1.put(envelope)

        envelope = multiplexer2.get(block=True, timeout=1.0)
        msg = DefaultSerializer().decode(envelope.message)
        assert envelope.protocol_id == "default"
        assert msg.get("content") == b"hello"
        envelope = multiplexer2.get(block=True, timeout=1.0)
        msg = FIPASerializer().decode(envelope.message)
        assert envelope.protocol_id == "fipa"
        assert msg.get("performative") == FIPAMessage.Performative.CFP
        envelope = multiplexer2.get(block=True, timeout=1.0)
        msg = FIPASerializer().decode(envelope.message)
        assert envelope.protocol_id == "fipa"
        assert msg.get("performative") == FIPAMessage.Performative.PROPOSE
        envelope = multiplexer2.get(block=True, timeout=1.0)
        msg = FIPASerializer().decode(envelope.message)
        assert envelope.protocol_id == "fipa"
        assert msg.get("performative") == FIPAMessage.Performative.ACCEPT
        envelope = multiplexer2.get(block=True, timeout=1.0)
        msg = FIPASerializer().decode(envelope.message)
        assert envelope.protocol_id == "fipa"
        assert msg.get("performative") == FIPAMessage.Performative.DECLINE
        multiplexer1.disconnect()
        multiplexer2.disconnect()


@pytest.mark.asyncio
async def test_connecting_to_node_with_same_key():
    """Test that connecting twice with the same key works correctly."""
    with LocalNode() as node:
        address = "my_address"
        my_queue = asyncio.Queue()

        ret = await node.connect(address, my_queue)
        assert ret is not None and isinstance(ret, asyncio.Queue)
        ret = await node.connect(address, my_queue)
        assert ret is None
