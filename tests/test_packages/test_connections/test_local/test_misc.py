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

from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer

from packages.fetchai.connections.local.connection import LocalNode
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.message import FipaMessage

from tests.conftest import _make_local_connection


def test_connection():
    """Test that two OEF local connection can connect to a local node."""
    with LocalNode() as node:

        multiplexer1 = Multiplexer(
            [_make_local_connection("multiplexer1", "my_public_key_1", node)]
        )
        multiplexer2 = Multiplexer(
            [_make_local_connection("multiplexer2", "my_public_key_2", node)]
        )

        multiplexer1.connect()
        multiplexer2.connect()

        multiplexer1.disconnect()
        multiplexer2.disconnect()


@pytest.mark.asyncio
async def test_connection_twice_return_none():
    """Test that connecting twice works."""
    with LocalNode() as node:
        address = "address"
        public_key = "public_key"
        connection = _make_local_connection(address, public_key, node)
        await connection.connect()
        await node.connect(address, connection._reader)
        message = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        expected_envelope = Envelope(to=address, sender=address, message=message,)
        await connection.send(expected_envelope)
        actual_envelope = await connection.receive()

        assert expected_envelope == actual_envelope

        await connection.disconnect()


@pytest.mark.asyncio
async def test_receiving_when_not_connected_raise_exception():
    """Test that when we try to receive an envelope from a not connected connection we raise exception."""
    with LocalNode() as node:
        with pytest.raises(ConnectionError):
            address = "address"
            public_key = "public_key"
            connection = _make_local_connection(address, public_key, node)
            await connection.receive()


@pytest.mark.asyncio
async def test_receiving_returns_none_when_error_occurs():
    """Test that when we try to receive an envelope and an error occurs we return None."""
    with LocalNode() as node:
        address = "address"
        public_key = "public_key"
        connection = _make_local_connection(address, public_key, node)
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

        multiplexer1 = Multiplexer(
            [_make_local_connection("multiplexer1", "multiplexer1_public_key", node)]
        )
        multiplexer2 = Multiplexer(
            [_make_local_connection("multiplexer2", "multiplexer1_public_key", node)]
        )

        multiplexer1.connect()
        multiplexer2.connect()

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        envelope = Envelope(to="multiplexer2", sender="multiplexer1", message=msg,)
        multiplexer1.put(envelope)

        msg = FipaMessage(
            performative=FipaMessage.Performative.CFP,
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            query=Query([Constraint("something", ConstraintType(">", 1))]),
        )
        envelope = Envelope(to="multiplexer2", sender="multiplexer1", message=msg,)
        multiplexer1.put(envelope)

        msg = FipaMessage(
            performative=FipaMessage.Performative.PROPOSE,
            dialogue_reference=(str(0), ""),
            message_id=2,
            target=1,
            proposal=Description({}),
        )

        envelope = Envelope(to="multiplexer2", sender="multiplexer1", message=msg,)
        multiplexer1.put(envelope)

        msg = FipaMessage(
            performative=FipaMessage.Performative.ACCEPT,
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
        )
        envelope = Envelope(to="multiplexer2", sender="multiplexer1", message=msg,)
        multiplexer1.put(envelope)

        msg = FipaMessage(
            performative=FipaMessage.Performative.DECLINE,
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
        )
        envelope = Envelope(to="multiplexer2", sender="multiplexer1", message=msg,)
        multiplexer1.put(envelope)

        envelope = multiplexer2.get(block=True, timeout=1.0)
        msg = envelope.message
        assert (
            envelope.protocol_specification_id
            == DefaultMessage.protocol_specification_id
        )
        assert msg.content == b"hello"
        envelope = multiplexer2.get(block=True, timeout=1.0)
        msg = envelope.message
        assert (
            envelope.protocol_specification_id == FipaMessage.protocol_specification_id
        )
        assert msg.performative == FipaMessage.Performative.CFP
        envelope = multiplexer2.get(block=True, timeout=1.0)
        msg = envelope.message
        assert (
            envelope.protocol_specification_id == FipaMessage.protocol_specification_id
        )
        assert msg.performative == FipaMessage.Performative.PROPOSE
        envelope = multiplexer2.get(block=True, timeout=1.0)
        msg = envelope.message
        assert (
            envelope.protocol_specification_id == FipaMessage.protocol_specification_id
        )
        assert msg.performative == FipaMessage.Performative.ACCEPT
        envelope = multiplexer2.get(block=True, timeout=1.0)
        msg = envelope.message
        assert (
            envelope.protocol_specification_id == FipaMessage.protocol_specification_id
        )
        assert msg.performative == FipaMessage.Performative.DECLINE
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


def test_stop_before_start():
    """Test stop called before start."""
    node = LocalNode()
    with pytest.raises(ValueError, match="Connection not started!"):
        node.stop()
