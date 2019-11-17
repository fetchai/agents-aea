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

"""This module contains the tests for the TCP base module."""
import asyncio
from asyncio import CancelledError

import aea
import pytest
import unittest.mock

from aea.connections.tcp.tcp_client import TCPClientConnection
from aea.connections.tcp.tcp_server import TCPServerConnection
from aea.mail.base import Envelope


@pytest.mark.asyncio
async def test_connect_twice():
    """Test that connecting twice the tcp connection works correctly."""
    tcp_connection = TCPServerConnection("public_key", "127.0.0.1", 8082)

    loop = asyncio.get_event_loop()
    tcp_connection.loop = loop

    await tcp_connection.connect()
    with unittest.mock.patch.object(aea.connections.tcp.base.logger, "warning") as mock_logger_warning:
        await tcp_connection.connect()
        mock_logger_warning.assert_called_with("Connection already set up.")

    await tcp_connection.disconnect()


@pytest.mark.asyncio
async def test_connect_raises_exception():
    """Test the case that a connection attempt raises an exception."""
    tcp_connection = TCPServerConnection("public_key", "127.0.0.1", 8082)

    loop = asyncio.get_event_loop()
    tcp_connection.loop = loop

    with unittest.mock.patch.object(aea.connections.tcp.base.logger, "error") as mock_logger_error:
        with unittest.mock.patch.object(tcp_connection, "setup", side_effect=Exception("error during setup")):
            await tcp_connection.connect()
            mock_logger_error.assert_called_with("error during setup")


@pytest.mark.asyncio
async def test_disconnect_when_already_disconnected():
    """Test that disconnecting a connection already disconnected works correctly."""
    tcp_connection = TCPServerConnection("public_key", "127.0.0.1", 8082)

    with unittest.mock.patch.object(aea.connections.tcp.base.logger, "warning") as mock_logger_warning:
        await tcp_connection.disconnect()
        mock_logger_warning.assert_called_with("Connection already disconnected.")


@pytest.mark.asyncio
async def test_send_to_unknown_destination():
    """Test that a message to an unknown destination logs an error."""
    public_key = "public_key"
    tcp_connection = TCPServerConnection(public_key, "127.0.0.1", 8082)
    envelope = Envelope(to="non_existing_destination", sender="public_key", protocol_id="default", message=b"")
    with unittest.mock.patch.object(aea.connections.tcp.base.logger, "error") as mock_logger_error:
        await tcp_connection.send(envelope)
        mock_logger_error.assert_called_with("[{}]: Cannot send envelope {}".format(public_key, envelope))


@pytest.mark.asyncio
async def test_send_cancelled():
    """Test that cancelling a send works correctly."""
    tcp_server = TCPServerConnection("public_key_server", "127.0.0.1", 8082)
    tcp_client = TCPClientConnection("public_key_client", "127.0.0.1", 8082)

    await tcp_server.connect()
    await tcp_client.connect()

    with unittest.mock.patch.object(tcp_client._writer, "drain", side_effect=CancelledError):
        envelope = Envelope(to="public_key_client", sender="public_key_server", protocol_id="default", message=b"")
        await tcp_client.send(envelope)

    await tcp_client.disconnect()
    await tcp_server.disconnect()
