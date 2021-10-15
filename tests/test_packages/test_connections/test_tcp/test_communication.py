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

"""This module contains the tests for the TCP connection communication."""

import asyncio
import struct
import unittest.mock

import pytest

from aea.mail.base import Envelope
from aea.multiplexer import Multiplexer

from packages.fetchai.protocols.default.message import DefaultMessage

from tests.conftest import (
    _make_tcp_client_connection,
    _make_tcp_server_connection,
    get_unused_tcp_port,
)


class TestTCPCommunication:
    """Test that TCP Server and TCP Client can communicate."""

    @classmethod
    def setup_class(cls):
        """Set up the test class."""
        cls.host = "127.0.0.1"
        cls.port = get_unused_tcp_port()

        cls.server_addr = "server_addr"
        cls.server_public_key = "server_public_key"
        cls.client_addr_1 = "client_addr_1"
        cls.client_public_key_1 = "client_public_key_1"
        cls.client_addr_2 = "client_addr_2"
        cls.client_public_key_2 = "client_public_key_2"

        cls.server_conn = _make_tcp_server_connection(
            cls.server_addr, cls.server_public_key, cls.host, cls.port,
        )
        cls.client_conn_1 = _make_tcp_client_connection(
            cls.client_addr_1, cls.client_public_key_1, cls.host, cls.port,
        )
        cls.client_conn_2 = _make_tcp_client_connection(
            cls.client_addr_2, cls.client_public_key_2, cls.host, cls.port,
        )

        cls.server_multiplexer = Multiplexer([cls.server_conn])
        cls.client_1_multiplexer = Multiplexer([cls.client_conn_1])
        cls.client_2_multiplexer = Multiplexer([cls.client_conn_2])

        assert not cls.server_conn.is_connected
        assert not cls.client_conn_1.is_connected
        assert not cls.client_conn_2.is_connected

        cls.server_multiplexer.connect()
        cls.client_1_multiplexer.connect()
        cls.client_2_multiplexer.connect()

    def test_is_connected(self):
        """Test that the connection status are connected."""
        assert self.server_conn.is_connected
        assert self.client_conn_1.is_connected
        assert self.client_conn_2.is_connected

    def test_communication_client_server(self):
        """Test that envelopes can be sent from a client to a server."""
        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        expected_envelope = Envelope(
            to=self.server_addr, sender=self.client_addr_1, message=msg,
        )
        self.client_1_multiplexer.put(expected_envelope)
        actual_envelope = self.server_multiplexer.get(block=True, timeout=5.0)

        assert expected_envelope.to == actual_envelope.to
        assert expected_envelope.sender == actual_envelope.sender
        assert (
            expected_envelope.protocol_specification_id
            == actual_envelope.protocol_specification_id
        )
        assert expected_envelope.message != actual_envelope.message
        msg = DefaultMessage.serializer.decode(actual_envelope.message)
        msg.to = actual_envelope.to
        msg.sender = actual_envelope.sender
        assert expected_envelope.message == msg

    def test_communication_server_client(self):
        """Test that envelopes can be sent from a server to a client."""
        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        expected_envelope = Envelope(
            to=self.client_addr_1, sender=self.server_addr, message=msg,
        )
        self.server_multiplexer.put(expected_envelope)
        actual_envelope = self.client_1_multiplexer.get(block=True, timeout=5.0)

        assert expected_envelope.to == actual_envelope.to
        assert expected_envelope.sender == actual_envelope.sender
        assert (
            expected_envelope.protocol_specification_id
            == actual_envelope.protocol_specification_id
        )
        assert expected_envelope.message != actual_envelope.message
        msg = DefaultMessage.serializer.decode(actual_envelope.message)
        msg.to = actual_envelope.to
        msg.sender = actual_envelope.sender
        assert expected_envelope.message == msg

        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"hello",
        )
        expected_envelope = Envelope(
            to=self.client_addr_2, sender=self.server_addr, message=msg,
        )
        self.server_multiplexer.put(expected_envelope)
        actual_envelope = self.client_2_multiplexer.get(block=True, timeout=5.0)

        assert expected_envelope.to == actual_envelope.to
        assert expected_envelope.sender == actual_envelope.sender
        assert (
            expected_envelope.protocol_specification_id
            == actual_envelope.protocol_specification_id
        )
        assert expected_envelope.message != actual_envelope.message
        msg = DefaultMessage.serializer.decode(actual_envelope.message)
        msg.to = actual_envelope.to
        msg.sender = actual_envelope.sender
        assert expected_envelope.message == msg

    @classmethod
    def teardown_class(cls):
        """Tear down the test class."""
        cls.server_multiplexer.disconnect()
        cls.client_1_multiplexer.disconnect()
        cls.client_2_multiplexer.disconnect()


class TestTCPClientConnection:
    """Test TCP Client code."""

    @pytest.mark.asyncio
    async def test_receive_cancelled(self):
        """Test that cancelling a receive task works correctly."""
        port = get_unused_tcp_port()
        tcp_server = _make_tcp_server_connection(
            "address_server", "public_key_server", "127.0.0.1", port,
        )
        tcp_client = _make_tcp_client_connection(
            "address_client", "public_key_client", "127.0.0.1", port,
        )

        await tcp_server.connect()
        await tcp_client.connect()

        with unittest.mock.patch.object(tcp_client.logger, "debug") as mock_logger:
            task = asyncio.ensure_future(tcp_client.receive())
            await asyncio.sleep(0.1)
            task.cancel()
            await asyncio.sleep(0.1)
            mock_logger.assert_called_with(
                "[{}] Read cancelled.".format("address_client")
            )
            assert task.result() is None

        await tcp_client.disconnect()
        await tcp_server.disconnect()

    @pytest.mark.asyncio
    async def test_receive_raises_struct_error(self):
        """Test the case when a receive raises a struct error."""
        port = get_unused_tcp_port()
        tcp_server = _make_tcp_server_connection(
            "address_server", "public_key_server", "127.0.0.1", port,
        )
        tcp_client = _make_tcp_client_connection(
            "address_client", "public_key_client", "127.0.0.1", port,
        )

        await tcp_server.connect()
        await tcp_client.connect()

        with unittest.mock.patch.object(tcp_client.logger, "debug") as mock_logger:
            with unittest.mock.patch.object(
                tcp_client, "_recv", side_effect=struct.error
            ):
                task = asyncio.ensure_future(tcp_client.receive())
                await asyncio.sleep(0.1)
                mock_logger.assert_called_with("Struct error: ")
                assert task.result() is None

        await tcp_client.disconnect()
        await tcp_server.disconnect()

    @pytest.mark.asyncio
    async def test_receive_raises_exception(self):
        """Test the case when a receive raises a generic exception."""
        port = get_unused_tcp_port()
        tcp_server = _make_tcp_server_connection(
            "address_server", "public_key_server", "127.0.0.1", port,
        )
        tcp_client = _make_tcp_client_connection(
            "address_client", "public_key_client", "127.0.0.1", port,
        )

        await tcp_server.connect()
        await tcp_client.connect()

        with pytest.raises(Exception, match="generic exception"):
            with unittest.mock.patch.object(
                tcp_client, "_recv", side_effect=Exception("generic exception")
            ):
                task = asyncio.ensure_future(tcp_client.receive())
                await asyncio.sleep(0.1)
                assert task.result() is None

        await tcp_client.disconnect()
        await tcp_server.disconnect()


class TestTCPServerConnection:
    """Test TCP Server code."""

    @pytest.mark.asyncio
    async def test_receive_raises_exception(self):
        """Test the case when a receive raises a generic exception."""
        port = get_unused_tcp_port()
        tcp_server = _make_tcp_server_connection(
            "address_server", "public_key_server", "127.0.0.1", port,
        )
        tcp_client = _make_tcp_client_connection(
            "address_client", "public_key_client", "127.0.0.1", port,
        )

        await tcp_server.connect()
        await tcp_client.connect()
        await asyncio.sleep(0.1)

        with unittest.mock.patch.object(tcp_server.logger, "error") as mock_logger:
            with unittest.mock.patch(
                "asyncio.wait", side_effect=Exception("generic exception")
            ):
                result = await tcp_server.receive()
                assert result is None
                mock_logger.assert_any_call(
                    "Error in the receiving loop: generic exception"
                )

        await tcp_client.disconnect()
        await tcp_server.disconnect()
